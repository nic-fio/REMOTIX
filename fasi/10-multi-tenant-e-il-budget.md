# Phase 10 — Multi-tenant and the budget

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

Opened on **24 Aug 2026**, right after phase 9 was closed.
## ✅⭐⭐⭐⭐⭐ **CLOSED on 25 Aug 2026**, on the user's judgement

> *«Sono soddisfatto. Riprodotto audio e video su una connessione del 1990. **Non credo che si
> possa chiedere di più**.»*

> *«Allora la sessione ha raggiunto il suo scopo: il multitenant. **10 utenti contemporaneamente
> presenti su una GPU integrata è un risultato di assoluta eccellenza**.»*

⭐ The two judgements in full, with the numbers of the scenes they were given on, are in **§10**.
⚠ And **two decisions were left untaken**, declared in **§10-bis**: the defaults apply.

> ⛔ **This document is filled in along the way** (`PIANO.md` §0.1). The measurements have the time
> next to them because they were written when they were taken, and the **predictions of §2 were written
> BEFORE measuring** — it is the only way a measurement can refute anything.

---

## What it must produce

**Several users together, the encoder budget, the refusal with a reason** (`PIANO.md` phase 10).

**What the user sees and judges at the end**: two real sessions at the same time; and when the
machine is full, a message that **says why**.

| # | what | where it stood on the morning of 24 Aug 2026 |
|---|---|---|
| 1 | **the real number of the encoder** — pixels/s on `renderD128` | ⛔ never measured: `vainfo` says *which* profiles, not *how many pixels per second* |
| 2 | **the budget** in place of the count | ⛔ two `#define`s at **16**: `src/rcp.c:886 MAX_ATTACCATE`, `src/figlio.c:91 MAX_FIGLI` — where `SPECIFICHE.md` §5.5 promises **ten, configurable** |
| 3 | **`BUDGET_PIENO 0x06`** with the reason in the body | ⛔ declared in `src/rcp.h` · `RCP_BUDGET_PIENO` and in `RCP.md` §8.2, **and no line of the server ever sends it** |
| 4 | **whoever is already working does not get worse** when the eleventh arrives | ⛔ never tested — it is `DECISIONI.md` §4.6-bis and invariant **I1** |
| 5 | **the NETWORK budget** next to the GPU one | ⛔ never named: `DECISIONI.md` §3.1-bis point 2 leaves it open with *«dieci sessioni × 30 Mbit/s sono 300 Mbit/s sul filo del server»* |

> ### ⭐ The order was set by the director, on 24 Aug 2026
>
> *«Prima si misura, e poi simuli 10 utenti veri.»*
>
> ⛔ It is the method constraint of the whole phase, and it is not a preference: **the encoder's number
> cannot be guessed**. `DECISIONI.md` §4.6 says so itself — *«nessun numero cablato nel programma»* —
> and the table of `SPECIFICHE.md` §5.5 (*«una cinquantina al minimo, 8-10 a 1080p30, una sola a
> 4K60»*) is still `[?]`: derived from the chip generation, not read from a bench.
>
> ⇒ **First the measurement, then the ten real ones, and only at the end the product code.**

> ### ⛔ Why this phase sits HERE and not elsewhere — the three precedences, all already decided
>
> | | |
> |---|---|
> | **after phase 8** | zero copy changes **how much a session costs** in GPU memory and bandwidth, and a budget measured before zero copy is a budget to redo (`DECISIONI.md` §4.6-quater) |
> | **before the three new desktops** | ⛔ the budget is a GPU budget, and **the GPU is ONE** — `renderD128`, the same iGPU that composites **every** desktop. It is a property **of the machine**, not of the desktop: measured after three new desktops, one no longer knows which number belongs to what (§4.6-sexies, decided by the user on 16 Aug) |
> | **the border with phase 5 is intact** | *«un utente per volta»* stays with phase 5; *«la macchina piena»* belongs to this one (§4.6-quater) |

---

# ⭐⭐⭐ THE SUMMARY — *the first round of measurements, 24 Aug 2026*

> ⛔ **This is the head of the document: it answers quickly the questions that will be asked tomorrow.**
> The detail is below: §1 the bench, §2 the predictions and their verdict, §3 the design, §4 the adversarial
> lens, §6 the measurements.

## S.1 · ⭐⭐⭐⭐ THE FACT THAT OVERTURNS THE PHASE: **the bottleneck is not the encoder**

`DECISIONI.md` §4.6 builds the whole budget on one sentence: *«il limite vero lo pone il
**codificatore**, e si misura in pixel al secondo»*. ⛔ **`[M]` On this hardware it is not true.**

| | where the bottleneck is | measured |
|---|---|---|
| **the bare encoder** (synthetic scene, no compositor) | the two VDBOXes | **1.86 Gpixel/s** in H.264 (§6.2) · ⭐ **2.33 in HEVC**, which is what the product negotiates **first** (§6.10) |
| ⭐⭐⭐ **the COMPOSITING** | ⛔ **`rcs0`, the render engine** | ⭐ **0.97 Gpixel/s** (§6.11) — **half** of the encoder. A 1080p desktop at 60 Hz is worth **124.4 Mpixel/s** ⇒ `rcs0` passes **99 % at the seventh** |
| with **real GNOME desktops** behind | the same thing, seen from the other end | it gives way at **six** sessions, and the **video** engine never passes **27 %** (§6.5) |

⭐⭐⭐ **And two different benches, on two different quantities, give the same answer**: §6.5 counts the
**sessions** and finds **six**; §6.11 counts the **composited pixels** and finds that the **seventh** saturates
`rcs0`. ⇒ **The number is not an accident of the bench: it belongs to the hardware.**

⭐⭐ **And our colour conversion is ACQUITTED** (§6.11): `[M]` **zero** on `rcs0`, all on the
**VEBOX**, which is never the bottleneck. ⚠ §6.6 had found it on the EUs — but that was `ffmpeg` with
`hwupload` of 8 MB per frame, whereas **the product imports a dmabuf at zero copy**
(`LEZIONI.md` §1.28: two different scenes, both true).
⇒ ⛔ **What saturates `rcs0` is the COMPOSITOR, and it alone is enough** — that is, something that **is not ours**, and that
the budget can only **count**, not reduce.

⭐⭐ **And the cost has TWO terms, not one** (§6.11): `[M]` `rcs0 % ≈ 7,1 % fisso + 0,053 % per
Mpixel/s` ⇒ **half the cost is a toll for merely being a live desktop at 60 Hz**, and 6.5 times
the change costs **1.68** times. It is the fixed term that decides how many quiet sessions fit.

## S.2 · ⭐⭐⭐⭐ **SIX on the worst scene, ELEVEN on the real one — and eleven is not the limit**

> *«Tenendo conto che siamo su una scheda Intel integrata non particolarmente performante, 6 RDP
> attivi contemporaneamente non mi sembra un cattivo risultato»* — the user, **24 Aug 2026**,
> `DECISIONI.md` **§4.6-septies**. ⇒ ⭐ **The judgement comes out strengthened, not refuted.**

| scene | how many fit | what happens to the first |
|---|---|---|
| **saturated** — the whole screen changes at every frame | **6** | ⛔ from the seventh it gives way: −28 %, then **1.5 fps** at the eighth |
| ⭐⭐ **real desktop** — windows, drags, tears | ⭐ **at least 11**, and ⛔ **the ceiling was not found: the users ran out, not the machine** | ⭐ **−7.7 %**, under the tolerance, and the **latency does not move** (8.4 → 8.0 ms) |
| **still** | ⭐ **11 cost ZERO GPU** — RC6 100 %, GT 0 MHz | there the constraint is **memory**, not the card |

⭐⭐⭐ **The «six» was the number of a scene no user produces.** `[M]` On the real desktop: **zero
violations of invariant I1** at eleven sessions, against **37** on the saturated one; and eleven sessions
sit at **22-24 %** of the GPU (§6.12).

⛔ **And the cliff exists only on the saturated scene**: between the sixth and the eighth one goes from 38 to 1.5 fps
— **it is not degradation, it is a precipice**, and the phase 9 ladder does not soften it.
⇒ ⭐ **The product must stop BEFORE the cliff, not inside it** — and this, not «ten», is the work
of the phase.

⛔ **And today it does not stop at all**: the eleventh of the saturated scene **gets in with `negati 0`**, and the
first session goes from 39.60 to 0.96 fps (**−97.6 %**). **The product has no budget: it accepts
everyone and starves everyone together.**

## S.3 · ⭐⭐⭐⭐ THE CLIFF HAS A MECHANISM, and it is **a threshold the product can compute**

⭐⭐ **The proof is in one line**: same population — eight sessions, eight desktops, eight children — and
**one single scene is switched off**. `[M]` **The rate comes back from 1.6 to 33.4 fps.** Putting it back, the cliff
reproduces. **Reversible and repeatable** (§6.15).

⇒ ⛔ **The cliff does not fall on the number of sessions: it falls on how much is being COMPOSITED.** `[M]` The border
lies between **421 and 460 draws/s** at 1080p, that is **0.87-0.95 Gpixel/s** — ⭐⭐⭐ **and it falls exactly on the
compositing ceiling measured by another bench, 0.97** (§6.11).

⭐ **And the column that betrays it is the one nobody was looking at**: when the compositors take
100 % of the drawing engine, `video-enhance` **collapses from 48.7 % to 0.4 %** ⇒ ⛔ **the encoder has
nothing left to do. It does not slow down: it stops.** The stage deliveries go from **39 to 2 fps**.
⇒ **The bottleneck is not in the parent and not in the encoder: it is upstream, in the compositing** — that is, in
something that **is not ours**.

⛔ **Five leads out of six were false**, and they were refuted one by one: the software fallback,
a wait that becomes everyone's latency, the queue threshold, the rate regulator, the parent's
loop. ⭐⭐ **Including the buffer arithmetic, which looked the best and was refuted by the one who had
proposed it**: `[M]` the producer gives **eight**, not six ⇒ we are **never** left without buffers.

⚠ **And the degradation does not go through the column phase 9 had taught us to watch**: `[M]` **zero
keyframes out of 8 741**, even inside the collapse — what moves is the **latency**.
⇒ ⭐ The rule of `LEZIONI.md` §1.31 holds, **the column does not**: which mechanism it is **changes with the
phenomenon**, and must be looked for every time (§1.34).

## S.4 · ⛔ The product defects found, and **none of them was the target**

> ### ⛔⛔⛔ AND THE TWO MOST SERIOUS ARRIVED LAST — *25 Aug 2026, evening*
>
> | | |
> |---|---|
> | ⛔⛔⛔ **THE SESSION THAT IS BORN BLIND** (§7.4) | `[M]` On a **newborn** session Mutter announces no `wl_output` ⇒ **no application can open a window**. Firefox stays alive and never paints; the compositor sits at **0.0 %**; zero frames. ⚠ **Intermittent**: `provanic3` got the monitor **2 times and then 6 times not**; `provanic4/5/6` **never**, over 98 · 55 · 50 attempts. ⭐ Four hypotheses refuted one by one |
> | ⭐ *(refuted on 29 Sep 2026 by measurement T2 of phase 17: stopping the server does NOT take the desktops away — `fasi/17-l-installatore.md` §5.2)* ⛔⛔ **STOPPING THE SERVER TAKES AWAY ALL THE SESSIONS** (§7.5) | `[M]` Updating 7730 at **18:14:29**, the user's session died with the unit — windows included. ⇒ **Today updating the server means throwing everyone out**, and it is the damage `DECISIONI.md` §4.7 forbids anyone to cause |
>
> ⭐⭐ **And it was the DIRECTOR who brought them out**, by asking for a test that forced us to **start from zero** —
> ⛔ something that in the whole phase **had never been done**. The lesson is `LEZIONI.md` **§1.39**, and it is
> the reason for **phase 11**.
>
> ⚠ **What they do NOT touch**: the capacity numbers of §6 and §10, taken on sessions that **really
> drew**. ⛔ **What they touch**: the delivery.

| | |
|---|---|
| ⛔⛔ **the eleventh is ADMITTED and does not see a pixel** | the two `16`s are freed on **different events**: the children table can be full while the slots table is empty ⇒ black page **with nothing on the wire**, and no time after which it gets better (§4.1) |
| ⛔⛔⛔ **the child dies of SIGSEGV on an arbitrary width** | ⭐ **and it has nothing to do with multi-tenant: it concerns everyone.** `[M]` View **1268** — the one Firefox opens on its own — ⇒ DMA-BUF stride **5072, not a multiple of 64** ⇒ the child declares *«rimonto il palco sulla MEMORIA»* and **2 ms later it is dead**: **3 out of 3**, against **0 out of 3** at 1280. The user loses the desktop **before the first frame** (§6.8) |
| ⛔⛔⛔ **two phase 9 cures form a CLOSED LOOP that evicts whoever is working** | `[M]` At **five** sessions, **five clients evicted in 1.3 s**: `arretrato` stays glued to the regulator's cap, which blocks **every** frame ⇒ `usciti_byte=0` ⇒ the client **has nothing left to acknowledge**, goes silent ⇒ **the dead line evicts it with `persi=0`**. ⛔ Here the queue **bites**, that is, these are users who were working (§6.15) |
| ⚠ **two phase 9 cures fight each other — but only for the test client** | `linea-morta causa=silenzio … persi=0`, desktop still and loss **zero**, session closed at **10 s** with `aioquic` (§6.3). ⭐ **On real Firefox it survives** at 120 s and at 300 s (§6.8) — ⛔ **but because it is OUR `PING`s that keep it alive**, not the browser: the margin is **twice**, and no more |
| ⛔ **the desktop is switched on for someone who will never be admitted** | `[M]` a user **never admitted** at the end of the round had **42 processes and a `gnome-shell`** (§6.4) |
| ~~the second closing route of §3.1 does not start~~ ⇒ ✅ **WITHDRAWN** | `[M]` §6.8: with **real Firefox** the capsule arrives **10 out of 10**, code `0x0E`, never `0`. *«0 capsule»* was true **for `aioquic`**, which leaves **498 ms before** the capsule starts. ⛔ **The lesson is one of method**: it had been read **where the capsule leaves** instead of **where it arrives** |

## S.5 · ⭐ The three estimates of the documents that were wrong, and all **in the comfortable direction**

| where | it said | `[M]` |
|---|---|---|
| `SPECIFICHE.md` §5.5 · `DECISIONI.md` §4.6 | 1080p30: «8-10, giusto al limite» | the encoder fits at **33 %** — ⛔ but the machine stops at **six**, for another reason |
| `DECISIONI.md` §4.6 | «dieci sessioni GNOME ferme sono ~12 GB dei 31» | **1.8-1.9 GB** — wrong by **six times** |
| `DECISIONI.md` §3.1-bis point 2 | «dieci × 30 Mbit/s = 300 Mbit/s sul filo» | **22 Mbit/s**, **0.2 %** of a 10 Gbit/s card |

## S.6 · ⭐⭐⭐ HOW THE BUDGET IS WRITTEN — **and then it was written**

⛔ *Written after the two rounds of measurements only, when `src/` was still untouched: the director's order
was «prima si misura».*

> ### ⭐⭐ AND THEN: *«prima applica le patch, poi scrivi il prodotto e dopo rifai i test»*
>
> ⇒ The budget **is in the product** (`src/budget.c`, `src/budget.h`), with its three knobs; the
> `#define`s at 16 have become **one**; `BUDGET_PIENO 0x06` **really leaves**. What was
> built is in **§5**, the cures in **§5.1-5.13**.

⭐⭐ **And the shape of the budget is now measured, not hypothesised:**

| | |
|---|---|
| **the quantity** | ⛔ **not ENCODING pixels: COMPOSITING pixels.** `[M]` ceiling **0.97 Gpixel/s**, and what saturates it is **the compositor**, not us |
| **the currency** | ⭐ **the pixel**: at the give-ways the Mpixel/s match within **0.6 %** as the canvas varies, the frames/s differ by **74.9 %** |
| **how it adds up** | ⭐⭐ `[M]` **linearly, even across different roles**: three saturated + three real desktops give **75.3 % predicted against 75.6 % measured** |
| **the cost per role** | saturated **14.4 %** · real desktop **10.7 %** · ⭐ **still 0.01 %** |
| **the guard needed before the pixels** | ⛔ **the LATENCY**: the count on pixels, after the cliff, says *«c'è posto»* while everyone sits at 1.5 fps. `[M]` healthy ≤ **13.1 ms**, broken ≥ **39.9**, **no overlap** |
| **what the budget CANNOT foresee** | ⛔⛔ **the wake-up**: eight still ones admitted at 0.01 % each switch on in **19 ms** and ask for **130 %**. ⭐ The 50 % reserve limits the overshoot to **2×** |
| ⛔ **and what does not self-calibrate** | the capacity: **before the machine has given way once, it is a lower bound, not a ceiling** |

---

## §0 · THE STATE AT OPENING — *24 Aug 2026, 15:58 UTC*

### 0.1 ⭐ The machine was cleared **before** measuring, and verified

⛔ It is the rule paid for twice in one day (`LEZIONI.md` §1.26) and written in `PIANO.md`: *«quattro
server di prova degli agenti sono rimasti accesi… non danno fastidio a riposo, ma **falserebbero la
prossima misura**»*.

`[M]` At the closing of phase 9 the machine carried **eight** live `remotix-*` units from the benches of
that phase — ports 7900, 7910, 7920, 7940, 7950, 7960, 7971, 7973 — and **three children** still
attached (`provanr4`, `provanr8`, `provanr10`), the oldest for **1 day and 7 hours**.

All switched off. `[M]` **Verified, not declared from memory**:

```
--- porte 7xxx rimaste ---        NESSUNA
--- processi remotix rimasti ---  NESSUNO
--- netem su lo ---               qdisc noqueue 0: root refcnt 2      (nessun guasto residuo)
--- netem su enp7s0 ---           qdisc mq 0: root                    (nessun guasto residuo)
```

`[M]` Memory after the clearing: **12 GB used out of 31**, 18 available. Load average **0.10**.

### 0.2 ⛔ The hardware, and the card on which we do NOT measure

| | PCI address | node | what it is |
|---|---|---|---|
| ✅ **measured here** | `0000:00:02.0` | `renderD128` | **Intel UHD 730** (`i915`), the integrated one |
| ❌ excluded | `0000:03:00.0` | `renderD129` | Radeon **RX 6800** (`amdgpu`), group `remotix-nogpu` |

`[M]` The udev rule of `DECISIONI.md` §4.6-ter is **still applied**: `renderD129` belongs to the
group `remotix-nogpu`, which has no members. ⭐ It is the constraint set by the user on 15 Aug —
*«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco»*.

### 0.3 ⛔ The missing tool, and the route that remains

`[M]` **`intel_gpu_top` is not installed**, neither on the machine nor inside the container. `vainfo`,
`ffmpeg` and `gnome-shell` are there.

⇒ The occupancy of the GPU engines must be read from `/proc/<pid>/fdinfo/<fd>` (`drm-engine-*` on
`i915`), which gives cumulative nanoseconds per client. ⛔ **And it must be calibrated before believing it**
(`LEZIONI.md` §1.33): it is a number, not yet a measurement.

---

## §1 · THE BENCH — *written BEFORE developing*

`PIANO.md` §0.1. Ten benches, ten separate isolations, and ⛔ **a new lock** that is the
condition of the whole phase.

### 1.1 ⛔⛔ The GPU lock — the condition that governs the ten benches

**The GPU is one, and ten benches want it.** Two GPU loads together do not share the work:
they distort each other **silently**, and it is the exact wound of `LEZIONI.md` §1.26 — *a bench that measures while
another saturates does not give red, it gives a plausible number*.

⭐ We reuse the mechanism phase 9 had built for `netem`, `banchi/09-lucchetto.py`,
pointed at a place of its own:

```
LUCCHETTO=/media/REMOTIX/tmp/.lucchetto-gpu.d
```

⛔ **And the rule of use is stricter than «take it»**: *every round from which a number comes out that will be
reported takes the lock; for development and tuning one works without it, **but those numbers
do not count and are not reported***. A hold without expiry would block everyone until tomorrow;
the expiry is inside, and whoever finds it past **breaks in, declaring it**.

### 1.2 The catalogue of the phase's benches

| bench | what it measures | isolation |
|---|---|---|
| `10-b0-terreno` | ⛔ the check that looks **underneath** the other nine: idle machine, lock, right GPU, no leftover `netem`, binary newer than the sources, `ngtcp2` from the right place, free slot, ban not triggered | no port |
| `10-b87` | ⛔ **the GPU meter**, and its **calibration** with a known load (0, 1, 2, 4 streams; and one at half rate) | no port |
| `10-b88` | **the saturator**: ramp of N streams with the **product's** encoder, in **H.264**, at 480p25 · 1080p30 · 4K60, until it gives way — and ⛔ **why** it gives way | no port |
| `10-b89` | **how much ONE session costs** after zero copy: memory (PSS), GPU, CPU, wire, and what the user sees | port 8010 · `provadec1` |
| `10-b90` | **the network budget**: bits/s per session on three scenes, the **calibrated** meter, and the machine's real ceiling | port 8020 · `provadec2` |
| `10-b91`/`10-b92` | ⭐ **the ten real ones**: ten users, ten GNOME desktops, the climb from 1 to 10 with **every** session measured at **every** step | port 8100 · `provamt1…10` |
| `10-b93` | **the full table**: what reason the newcomer receives, what sentence the page shows, and ⛔ whether whoever was inside gets worse | port 8030 · `provadec4/5/6` |
| `10-b94` | **the study of the hardware**: `vainfo` in full, the VDBOXes, the concurrent VA-API contexts, and what changes under load | no port |

And two read-only assignments, without a bench: **where the budget lives** in the code (the design, not the
code) and ⛔ **the adversarial lens** — *prove that multi-tenant is NOT ready*.

### 1.3 ⛔ The six rules the ten benches carry

They come from the five lessons paid for in phase 9 (`LEZIONI.md` §1.29-§1.33), and they are not advice:

1. ⛔ **A bench is not finished until it has been seen giving RED.** Nine bench defects out of nine,
   in phase 9, had the shape *«silence instead of red»*: none made a bench **fail**,
   all made it **go quiet**;
2. ⛔ **`None` is not zero.** «I could not measure» ≠ «nothing happened»;
3. ⛔ **The meter is calibrated FIRST**, by injecting a known value;
4. ⛔ **One counts how much stress ARRIVED** before declaring a result;
5. ⭐ **The mechanism goes next to the symptom**: in phase 9 there was a factor of **five** between the two;
6. ⚠ **Short rounds underestimate**: the user's sessions last hours, the benches twenty-five seconds.

### 1.4 ⭐ THE GROUND CHECK — `10-b0`, and **30 faults out of 30 make it bite**

`banchi/10-b0-terreno.sh` (+ `10-b0-certifica.sh`, `10-b0-innesta.sh`). It is called like this:

```
CHI=10-a4 PORTA=8020 UTENTE=provadec2 ALBERO=/media/REMOTIX/src/10a4-src \
  bash banchi/10-b0-terreno.sh || exit 1
```

⛔ **Three exits, and the third is the one that counts**: `0` holds · `1` does not hold · **`2` I could not
verify**. **21 predicates** in eight groups: idle machine (load, memory, other people's `remotix`
**with name and user**, ports) · **GPU lock** (whose it is, how long is left, and `LUCCHETTO_MIO=1`
if a number comes out of the round) · right GPU (PCI addresses, `remotix-nogpu` fence, group without
members, **who holds the discrete one open**) · `netem`/wondershaper on `lo` **and** on `enp7s0` · **code
= what I read** (R12.3, local↔remote md5, newer binary, single binary) · `ldd` from `b2` ·
free slot (stage, clients) · ban of §4.4-bis.

`[M]` **30 faults out of 30 made the check bite**, in 50 rounds, **three times in a row**: among
them the fake lock of *«10-zz-intruso»* (red with the name) · the **expired** lock (green, but
it **declares** it and does not break in) · the binary older than a `.c` · the two copies of `rcp.c`
diverging · a process holding the **Radeon** open · the ban at 12 hours · ⭐ and the three cases that
unmask badly written checks — **ssh not answering**, **ssh with exit 0 and zero lines**,
**ssh dropped halfway**: all three give **exit 2**, never green.

> #### ⛔ The four things the certification taught — and the first is a defect found **in the check itself**
>
> 1. ⛔ **The defect was in the check**: the two DRM nodes were looked for with a two-branch `case`, and with
>    two equal PCI addresses the first branch won ⇒ the most important predicate of that section
>    became **UNKNOWN instead of looking at the card it had been named**. It is the shape **E8**.
>    Cured: they are looked for independently. ⭐ **It is exactly the reason a bench is certified.**
> 2. ⭐⭐ **The binary has NO rpath.** `[M]` Bare `ldd` on a built `remotix` resolves
>    `libngtcp2.so.16` from `/lib/x86_64-linux-gnu`, that is **from the system**: what brings it to `b2` is the
>    `LD_LIBRARY_PATH` the launchers export. ⇒ Reading **bare** `ldd` would give red on every
>    healthy tree; reading it **only with the environment** would hide that the choice depends **on who
>    starts it**. The check reads both and declares it. ⛔ The hole remains: **it does not see the command
>    line** with which the server will be started.
> 3. ⛔ **`bash -c "…; sleep N # segno"` loses the mark**: bash replaces itself with the last command, the
>    line becomes `sleep N`, `pgrep` does not find it and `pkill` does not kill it. ⇒ The fault **stayed
>    injected for 40 s and whoever had put it in believed they had not**. Now the mark sits in
>    `argv[0]` with `exec -a`.
> 4. ⚠ **A ground check must not load the machine it declares idle**: counting the fds
>    on the discrete card with one `readlink` per file would have been **~14 000 forks**. It is done with
>    `find -lname`, a single process, and the denominator is declared (`[M]` 1133 processes sifted).
>
> ⚠ **And two notes on the scene, which are not ours**: `pgrep -a -f 'remotix-figlio'` **catches its
> own command line**, and the test machine's profile prints `tput: No value for $TERM`
> on stderr at **every** `ssh` — with `2>&1` it ends up **inside the data**, and it already had.

**The holes the check declares** `[?]`: **the real GPU occupancy** it does not see ⇒ an agent
that measures on the GPU **without taking the lock is invisible to this check** · of the ban it sees
**only the file**, not the memory of the running server · ⛔ **it is a photograph**: that nothing changes between the check and
the measurement nobody guarantees — the lock is the only part that lasts.

---

## §2 · THE PREDICTIONS — *written on 24 Aug 2026, BEFORE any measurement*

> ⛔ **They are here because a prediction written afterwards is not a prediction.** Each one is falsifiable,
> and ⭐ **those that will be refuted are the most useful result of the phase**: in phase 9 the
> refuted predictions taught more than the ones that hit.

| # | prediction | how it is refuted |
|---|---|---|
| **Q1** | The ceiling measured in **H.264** will be **lower** than the table of `SPECIFICHE.md` §5.5, because that one is derived from the chip generation and takes no account of `EncSliceLP` nor of the **35 W** i5-13500T | `10-b88` gives 8-10 sessions at 1080p30 or more |
| **Q2** | ⛔ What gives way first **will not be the GPU**: it will be **memory** (ten GNOME sessions) or the **CPU** (ten times capture + QUIC), and the video engine will stay under 100 % | `10-b88` and `10-b89` show the video engine saturated before the other three quantities |
| **Q3** | **Ten sessions fit**, because `MAX_ATTACCATE` is already 16 and the architecture is *one process per session* — ⚠ but **not at 1080p30 all moving together** | `10-b92` stops below the tenth step |
| **Q4** | ⛔⛔ **Whoever was inside GETS WORSE when someone joins**, and in a way the frames/s do not show right away: the **keyframe share** will rise before the visible drop, as happened in phase 9 (factor of five between mechanism and symptom) | `10-b92` shows the first session steady on all columns up to the tenth step |
| **Q5** | ⛔ The **phase 9 cures turn against multi-tenant**: ten sessions contending for the same wire see each other **as a bad network**, each lowers its rate, and the **dead line** may end up **detaching** someone because the neighbour is working — where *«mai staccare»* is the only obligation that holds everywhere | `10-b90`/`10-b92` show no descent attributable to the neighbour |
| **Q6** | ⛔ The **ban by address** of §4.4-bis is a real multi-tenant defect: ten tenants behind the same NAT are **one single address**, and one who gets the password wrong three times throws the other nine out **for twelve hours** | reading the code shows it is keyed on the user too, or that the case does not arise |
| **Q7** | `MAX_FIGLI` **does not really follow** `MAX_ATTACCATE`: they are two separate `#define`s and the link lives only in the comment of `figlio.c` | `10-b93` shows that changing one changes the other |
| **Q8** | ⛔ The refusal at a full table arrives **after** something has already been switched on — *refusing after switching on a desktop is not refusing* | `10-b93` shows the no arrives before the child is born |
| **Q9** | The **network budget** bites **before** the GPU one: if the hard case in H.264 asks for **44.6 Mbit/s** (phase 9 §14.2), ten do not make 300 Mbit/s but **almost half a gigabit**, and the real ceiling is not the copper — it is the **CPU that encrypts** | `10-b90` measures a cost per session well under 30 Mbit/s on the real scenes |
| **Q10** | ⚠ The **log lines** do not say whose they are, and with ten sessions the log — which is the tool everything is diagnosed with in this project — becomes unreadable | sampling shows that the majority of lines carry the user or the session identifier |

### 2.1 ⭐⭐ THE VERDICT ON THE TEN — **four refuted**, and they are the part that taught

| # | outcome | in one line |
|---|---|---|
| **Q1** | ⛔ **REFUTED** | the ceiling is **HIGHER**, and on all three rows: 1080p30 sits at **33 %**, not «giusto al limite» (§6.2) |
| **Q2** | ⛔ **HALF REFUTED, and the right half is the uncomfortable one** | what gives way **IS** the GPU (the CPU sits at 1.2 cores out of 20) — ⛔ **but not the encoder: the render engine** (§6.5, §6.6) |
| **Q3** | ⛔ **REFUTED** | **SIX** fit, not ten (§6.5) |
| **Q4** | ⭐ **CONFIRMED**, and in the worst way | −97.6 % at the first session. ⚠ **But not by the predicted route**: the keyframes **never switch on**, the degradation goes through the **latency** (§6.5) |
| **Q5** | ⭐ **CONFIRMED in substance, corrected in the mechanism** | what detaches is not the regulator but the **dead line**, and by the route of **silence** (§6.3) |
| **Q6** | ⭐ **CONFIRMED** by reading | *«IL NOME UTENTE NON CONTA»*, `rcp.c` · `posto_prendi()` (§4.2) |
| **Q7** | ⭐ **CONFIRMED** | 2 against 16, measured on the binary (§6.4) |
| **Q8** | ⭐ **CONFIRMED, and worse** | not «refusing after switching on a desktop»: **the desktop is switched on even for someone who will never be admitted** (§6.4) |
| **Q9** | ⛔ **REFUTED** | ten saturated sessions make **22 Mbit/s** on a 10 Gbit/s card: **0.2 % of the wire** (§6.3, §6.5) |
| **Q10** | ⭐ **CONFIRMED, and measured** | `[M]` **4.2 %** of the **diagnostic** lines is attributable, and the blind test says **0 names out of 4** (§6.7) |

---

## §3 · ⭐⭐ THE DESIGN — where the budget lives, read in the code *(24 Aug 2026)*

> ⛔ **Reading, not code**: the product is touched after the numbers. But when the numbers arrive,
> this says **exactly** where to put them. Every line carries `file:riga` **and** the name of the
> function, because a line number ages silently.

### 3.1 ⛔⛔ The admission border — and today the no arrives **after the login**

The chain, with what already exists after each step:

| step | where | afterwards, exists |
|---|---|---|
| `CIAO` | `rcp.c:1972 tratta_ciao()` | nothing: the user does not have a name yet |
| `ECCOMI` | `rcp.c:1833 manda_eccomi()` | ⭐ codec, depth and level negotiated: **the client decoder's ceiling is already known here** |
| `CREDENZIALI` | `rcp.c:2284 tratta_credenziali()` | the user name (`s->utente`, line 2333); PAM **asked**, not answered |
| PAM verdict | `main.c:332 consegna_verdetto()` | ⛔⛔ **`figli_assicura()` at `main.c` · `guarda_il_servizio_pam()` — the child IS BORN HERE**, before `AMMESSO` goes out on the wire |
| `AMMESSO` | `rcp.c` · `rcp_verdetto()` | the child has already `fork`+`exec`ed, has already dropped to the uid, has already opened the logind session and has already taken the stage (`figlio.c` · `figlio_vive()` → `figlio.c`) |
| `ATTACCA` | `rcp.c:2702 tratta_attacca()` | **here** the slot is taken: `posto_prendi()`, `rcp.c` · `tratta_attacca()` |
| `SESSIONE` | `rcp.c` · `tratta_attacca()` | canvas decided, video channel on |
| the encoder | `webtransport.c:4117 video_regola()` → `main.c:466 figli_video()` → `MSG_VIDEO` → `figlio.c:4306 codificatore_di()` | ⭐ **the VA-API context opens only here**, on `renderD128` (`figlio.c`) |

⛔ **Hence the fact that decides the design.** `POSTO_NIENTE_PIU_POSTI` triggers at `rcp.c` · `tratta_attacca()`, that is
when the user is **already authenticated**, the child is **already born**, `pam_open_session` has **already** passed
and mutter and PipeWire are **already** capturing. ⇒ **Refusing there is not refusing: it is logging in and then
kicking out.** ⭐ **Prediction Q8 is confirmed, and by reading.**

⭐ The right place for the capacity no is **before `figli_assicura()`** (`main.c` · `guarda_il_servizio_pam()`); the second
best is inside `tratta_attacca()` **before** `posto_prendi()`, and it costs a desktop mounted for
nothing. ⭐ And between `AMMESSO` and `SESSIONE` there is a window in which **the desktop is on but the GPU is not**.

### 3.2 ⛔⛔⛔ The most serious fact of the reading: **the phase 9 regulator does not lower the GPU cost**

The regulator lives in the **parent** (`webtransport.c:4190+`, `WT_RITMO_POSTI` at `:3404`) and decides that a
frame **does not leave**. ⛔ But that frame **has already been encoded by the child**.

⇒ **A session on a terrible network costs the GPU exactly as much as a session on fibre.** And the
counts of the frames sent already exist (`wt_video_conti()`, `webtransport.c`), so
hooking the budget onto them is the natural thing to do — ⛔ **and it would say there is room precisely when there
is none**. The number to count is **on the other side of the process border**: `us_codifica` in
`tratti_conta()`, `figlio.c` · `tratti_mediana()`, and today it ends up **only in the log**.

⛔ **And the ghost keeps encoding.** Capture stops only when the last WebTransport session
of that user dies (`webtransport.c` · `apri_http3()`, guard `wt_video_qualcuno_guarda()` at `:5747`,
which looks at `video_acceso` and **not** at the RCP state). A client silent for 30 s has **left the
slot** (`rcp.c:7529 posto_lascia()`) and **is still encoding**. ⇒ **slots occupied ≠ GPU load**, and
a count kept on `attaccate[]` **underestimates** — precisely in the scene in which the machine is struggling.

### 3.3 ⛔ The two `#define`s at 16 are **four**, plus an **8** that bites at **nine**

| # | where | quantity | bites at |
|---|---|---|---|
| 1 | `rcp.c:886 MAX_ATTACCATE 16` — `attaccate[]` at `:902` | RCP slots | 17 |
| 2 | `figlio.c:91 MAX_FIGLI 16` — `v[MAX_FIGLI]` at `:519` | processes/stages | 17 |
| 3 | `aiutante.c:33 MAX_IN_VOLO 16` | ⚠ **authentications in flight**, not sessions | 17 **simultaneous**, with 0 active sessions |
| 4 | `main.c:706 QUANTI_PRESENTI 16` — `presenti[]` at `:709` | abandonment clock | 17, ⛔ **silently** (`main.c` · `deposita_fotogramma()`: `return` without a line) |
| ⛔ | `webtransport.c:5225 WT_PALCHI 8` — `palchi[]` | stage canvas for re-attach | ⛔⛔ **9 — that is, before the promised ten** |

⭐⭐ **Prediction Q7 is confirmed, and worse than it was written.** The comment of `figlio.c` —
*«quando quello diventerà un budget di pixel, questo lo seguirà dallo stesso posto»* — describes a
link **that does not exist in the code**: `MAX_ATTACCATE` is `static` in `rcp.c` and does not appear in
`rcp.h`; `MAX_FIGLI` is an independent literal. The same holds for `aiutante.c:29-32` (*«è lo
stesso `MAX_ATTACCATE` di `rcp.c`»* — it is not) and for `QUANTI_PRESENTI`.
⇒ **Four hand copies of the same number, three of which declare in writing a link that
the compiler does not know.**

⭐ And dismantling them costs little: the five functions that walk `attaccate[]` (`posto_occupato` 904,
`posto_chi` 913, `posto_prendi` 947, `posti_occupati` 965, `posto_lascia` 974) do **only linear
scans with `strcmp`** — no index arithmetic, no invariant on the 16. A `calloc` and a
module counter. ⛔ **The real constraint is another one**: `figli_descrittori()` (`figlio.c`)
fills the array of the parent's `poll`, and that is `MAX_POLL 64` (`main.c` · `TELA_A`) — see §3.6 item 10.

### 3.4 `BUDGET_PIENO 0x06` — and ⛔ **today the page says the sentence of a count**

`[M]` `grep RCP_BUDGET_PIENO src/*.c` → **no result**: declared at `rcp.h` · `RCP_VERSIONE` and in `RCP.md`
§8.2, **zero callers**. The model for sending it exists: `congeda()` (`rcp.c` · `utf8_valido()`) writes reason +
detail (lines 1658-1659), and `POSTO_NIENTE_PIU_POSTI` already uses it at `rcp.c:2856-2867`.

⛔ **And `src/pagina.html` · `MOTIVO()` says `0x06: "il server e' pieno"`** — it is not false, it is the sentence of a
**count**, where §4.6-bis decided *«questa macchina non ha più capacità di codifica»*.
⛔⛔ Worse: `0x0E` at `pagina.html` · `MOTIVO()` is *«quella sessione non si può servire»*, and it is **that one** the
user reads today at a full table — a sentence that speaks of **their** session while the fact
concerns the **server**.
⭐ The rest of the page holds: six places consult the `MOTIVO` table, there is always a fallback
*«congedato, motivo 0x…»*, and since 16 Aug every farewell brings back to the login form
(`pagina.html:5290-5300`) ⇒ **a `0x06` produces no hammering**.

⛔ **And `0x0E` does not become `0x06`**: they are two different facts, and it is finding **R9.3** (`rcp.c:920-938`).
*«La tabella dei posti è finita»* ≠ *«la macchina non ha più capacità di codifica»*.

### 3.5 The configurable cap — **two options, and it does not violate «one route only»**

| option | quantity | default |
|---|---|---|
| `--budget-mpixel-s N` | the **real limit**: encoding Mpixel/s this machine declares | ⛔ `[?]` **the number from the measurement** — not written until it exists. `0` = off, declared in the startup line |
| `--tetto-sessioni N` | the **administrative cap** of §4.6, and from it `attaccate[]`, `v[]`, `palchi[]`, `presenti[]` are sized | **10** (`SPECIFICHE.md` §5.5) |

⚠ Two and not one because they are **two quantities**, and `DECISIONI.md` §4.6 spells it out: *«dieci non
è il limite: è il tetto amministrativo. Il limite vero lo pone il codificatore»*. ⛔ What
would violate `CODER.md` §2-bis is **leaving the four `#define`s standing**: those really are the second
route, and they are already four numbers that can diverge.

⛔⭐ **And there is a third cap that does not exist today: the network one.** `--tetto-banda-mbit`
(`main.c` · `input_al_figlio()`) is a **floor per child**: `figli_fase9()` (`figlio.c` · `figli_accendi()`) copies it identically
into the `argv` of **every** child, and `codificatore.c:357 tetto_pavimento_mbit` is a **process**
static. ⇒ Ten children × 20 Mbit/s = **200 Mbit/s on the server's wire, and nobody knows it.** Point
5 of the phase has today **no line of code**.

### 3.6 ⛔ What breaks, ordered by **when** it bites

| # | what | where | bites at |
|---|---|---|---|
| 1 | ⛔⛔ **`WT_PALCHI 8`**: from the ninth user the stage canvas is not recorded, and at re-attach `SESSIONE` grants what the client asks for instead of what the stage has ⇒ §6.2 makes it **throw away every frame** until `ADATTA_TELA` arrives — *«riattacco e non vedo niente per un secondo»* | `webtransport.c` · `rete_ciclo()`, `palco_misura_segna()` `:5238` | ⛔ **9** |
| 2 | the **ghost that encodes** (§3.2): the budget counted on the slots underestimates the real load | `webtransport.c`, `:7208` | **at once** |
| 3 | the **regulator does not touch the GPU** (§3.2) | `webtransport.c:4190+` vs `figlio.c` · `tratti_mediana()` | **at once** |
| 4 | `--tetto-banda-mbit` **replicated per child** (§3.5) | `figlio.c` · `figli_accendi()` → `:5998` → `codificatore.c` · `BANDA_FINESTRA_US` | **at once**, visible at 3-4 |
| 5 | the **refusal after the login** (§3.1) | `main.c` · `guarda_il_servizio_pam()` vs `rcp.c` · `tratta_attacca()` | at every refusal |
| 6 | ⛔ the **findings folder is shared** and the file names are **fixed** (`cattura.bgrx`, `flusso-h264.264`, `scatto-*.bgrx`): two children with `--rilievo` on **overwrite each other**, and `SIGUSR1` is forwarded to **all** ⇒ the finding attributes to one user the pixels of another | `figlio.c` · `dichiara_priorita_audio()`, `:5595-5637`, `:1918-1929` | **2 users** (only with `--rilievo`) |
| 7 | ⛔ the **log lines do not say whose they are**: the header is `HH:MM:SS.mmm %-7s`, that is **only the area**, and parent and children **append to the same file**. Ten lines *«TRATTO cattura → byte fuori: mediana 3,2 ms»* per second, **indistinguishable** ⚠ and atomicity is guaranteed only under `PIPE_BUF` (4096), which this product's long lines come close to | `registro.c` · `riga()`, box `:37-58` | ⛔ **2**, unreadable at 10 — ⭐ **Q10 confirmed** |
| 8 | `presenti[]` **overflows silently**: the 17th user has no abandonment clock and **no line says so** | `main.c` · `deposita_fotogramma()`, `presenza_segna()` `:713`, mute `return` at `:730` | 17 |
| 9 | `MAX_IN_VOLO` is **another quantity** under the same number | `aiutante.c` · `rcp_autentica()` | 17 simultaneous, 0 sessions |
| 10 | ⛔ **`MAX_POLL 64` and the MUTE truncation of the children**: `figli_descrittori()` stops at `max` **without writing anything**. Worst count today 36 out of 64, the 16 children fit — ⛔ but beyond ~28 children, or with a crowded page, **a child stays out of the `poll` and its user no longer sees a pixel, without a line** | `main.c` · `TELA_A`, `figlio.c` | >28, and **silently** |
| 11 | ⛔ **nobody sees the software fallback**: if opening VA-API fails, the child falls back to `libx265` (much slower than the card — the measurement no longer holds after phase 18; today OpenH264, measured in `fasi/18-senza-ffmpeg.md` §5.4-§5.5; `figlio.c:4185-4188`) ⇒ the eleventh session can degrade **without the budget noticing**, and **I1 is broken for the newcomer** | `figlio.c` · `potenza_nome()`, `:4470` | `[?]`, depends on the driver |
| 12 | ⭐ the **ban file and the command socket do NOT break** (one single writer, one single socket) ⚠ but the ban is **per address**: ten users behind the same NAT share the three attempts | `main.c` · `presenza_segna()`, `comando.c` · `comando_descrittori()` | 1 NAT |

### 3.7 The `[?]` the reading does not close

| `[?]` | which measurement closes it |
|---|---|
| **how many pixels/s `renderD128` really sustains** — no line of the code knows it | the saturator `10-b88` |
| **the right quantity: pixels/s or engine occupancy** | two rounds at **equal pixels/s** with different codecs, and one in hardware against one fallen back: if the number of admissible sessions changes, the right quantity is the **occupancy** |
| **when the Intel driver stops giving VA-API contexts** | open N of them in N processes until `codificatore_nuovo()` fails, and read the fallback line of `figlio.c` · `codificatore_di()` — it is the assignment of `10-b94` |
| **whether `cattura_avvia()` costs GPU while nobody watches** | a live child without sessions, and `drm-engine-*` on `gnome-shell` |
| ⚠ **the aged comment of `figlio.c` · `potenza_nome()`** says *«non ci si arriva nella pratica»* and **it is reached**: `prendi_il_palco(primo=true)` calls `codifica_e_manda()` three times before every `MSG_VIDEO` | a log line at the birth of a child |

---

## §4 · ⛔⛔ THE ADVERSARIAL LENS — *«prova che il multi-tenant NON è pronto»* (24 Aug 2026)

> ⭐ Adversarial, read-only mandate: the thesis to refute was the one of `DECISIONI.md`
> §4.6-sexies — *«l'architettura c'è già in buona parte: un processo per sessione. Non si sta
> scansando una riscrittura strutturale»*.

### 4.0 The verdict in one line

⭐ **The thesis is half true.** *One process per session* really is there, and the three things that
looked shared — **clipboard, canvas, input** — are all routed **by user name** and do not
mix (§4.3, leads 5 and 8). ⛔ **But the count of users is kept in four places with four
different lives**, and the log — the project's only diagnostic tool — **stops saying whom it
is talking about as soon as there is more than one user**. It is not a structural rewrite: they are **five
seams**, and **two break the product at ten**.

### 4.1 ⛔⛔ R10-A1 · The eleventh is **ADMITTED** and does not see a pixel — and nothing goes out on the wire

**The fact**: the two `16`s **are freed on different events.** The slot in `attaccate[]` is freed at
detach (`posto_lascia()`, six routes); ⛔ **the child is not** — it is invariant **I4** (`figlio.h`):
it dies only by explicit logout or by abandonment at **60 minutes** without input (`main.c` · `consegna_verdetto()`).
⇒ **The children table can be full while the slots table is empty.**

**The scene**: morning, ten tenants come in, work, close the browser. The ten stages stay
alive for up to an hour. The eleventh passes PAM, receives `AMMESSO`, receives `SESSIONE`, the slot in
`attaccate[]` **is free** — and `figli_assicura()` (`main.c` · `guarda_il_servizio_pam()`) returns `false`. The code does not change
the verdict (it is declared, and it is defensible) and writes one single line: *«è AMMESSO ma non ha un figlio:
entra e non vede un pixel»*. ⛔⛔ **Nothing goes out on the wire**: neither `0x0E`, nor `0x06`. The user sees
a **black page without explanation**, and there is no time after which it gets better.

⛔ It is point 3 of the phase, and the trap concerns **how** it is closed: *if only the slot count
is replaced with the budget, the symptom will not be «budget full» — it will be a black screen without
a reason*, that is exactly the defect for which `posto_prendi()` had already been cured (R9.3).
⭐ **The model to resemble already exists**: `posto_prendi()` distinguishes «full» from «occupied» and sends
`0x0E` with the right reason. It is the seam done **well**.

### 4.2 The other findings, by severity

| # | what | where | bites |
|---|---|---|---|
| ⛔⛔ **R10-A2** | **The ban is per ADDRESS and ten tenants behind a NAT are one single address.** `rcp.c` · `posto_prendi()` declares it: *«IL NOME UTENTE NON CONTA. Tre nomi diversi contano tre»*. Three **different** tenants who get it wrong once each within five minutes **ban the address**: the other seven stay out for **12 hours** without having got anything wrong, and the only way out is the command socket, which is `0600` of **root** | `rcp.c:1052-1055`, `rcp_chiave_indirizzo()` `:1159`, check `:2364` | ⛔ **10 users in an office**. ⭐ **Q6 confirmed** |
| ⛔ **R10-A2-bis** | **A successful login removes the ban from memory but NOT from the file: the restart resurrects it.** `azzera_falliti()` does a `memset` of the whole entry, `bannato_fino` included, and ⛔ **does not call `salva_ban()`** — where its twin `rcp_sblocca()` does call it | `rcp.c` · `salva_ban()` vs `rcp.c` · `segna_fallito()` | ⚠ it does not break at once, **it lies later**: two truths about the same fact (**I7**) |
| ⛔⛔ **R10-A3** | **Ten tenants multiply the logind wait, and the DEAD LINE detaches them all.** `wt_sorveglia_locali()` loops over **all** sessions and for each one makes a **synchronous** D-Bus call, **inside the same `poll` that delivers the frames**; `ATTESA_MS` is 300. With one tenant the worst is 300 ms every 2 s; ⛔ **with ten it is 3 s every 2 s**. While the loop is stopped, `lm_usciti` does not rise for **any** session and `lm_offerti` keeps rising ⇒ past 5 s **`linea_morta_scatta()` throws out all ten**, each with the sentence *«la linea è MORTA»* — which **blames the user's network for a defect of the machine** | `webtransport.c` · `video_a_una()`, `main.c` · `ABBANDONO_PREDEFINITO_MS`, `sentinella.c` · `ATTESA_MS`, `webtransport.c` · `WT_RETE_PERDE` | ⛔ **10 users**, ⚠ **conditional** on a slow logind — but what triggers the condition is **the number of tenants** |
| ⛔ **R10-A4** | **The log does not say whose it is.** `gancio_registra()` receives the session context and **throws it away** (`(void)ctx;`); the format is `ora + area` and that is all — no pid, no user; the children **do not redirect `stderr`** and all ten append to the same file, with the **same area**. `[M]` static census: **79 %** of the lines of `rcp.c`, **63 %** of `webtransport.c`, **64 %** of `figlio.c` and ⛔ **100 %** of `codificatore.c` **without an identifier** | `webtransport.c` · `gancio_manda()`, `registro.c` · `riga()`, `figlio.c` · `diventa_ed_esegui()`, `figlio.h` · `REG_FIGLIO` | ⛔ **2 users**, unreadable at 10. ⭐ **Q10 confirmed, and with a number** |
| ⛔ **R10-A5** | **The bandwidth cap is PER TENANT, and nobody adds up**: `--tetto-banda-mbit 30` with ten tenants is not a cap of 30, it is a cap of **300**. In the whole of `src/` **there is no aggregate counter of the bytes sent out** | `main.c` · `consegna_verdetto()` → `:1544` → `figlio.c:1215-1217` | ⚠ today it does not break; it is **point 5 of the phase**, confirmed by the code |
| ⚠ **R10-A6** | **`WT_PALCHI` is EIGHT and the phase aims at ten**: the ninth and the tenth do not enter the table and at re-attach they receive the canvas **as the client asks for it** instead of as the stage has it. ⛔ And the fallback is declared **only once** (`palchi_pieni_detto`): the ninth and the tenth lose it **silently** | `webtransport.c` · `rete_ciclo()`, `palco_misura_segna()` `:5238` | ⚠ **9** — ugly, does not detach |
| ⚠ **R10-A7** | **`MAX_IN_VOLO` is 16 by copy, not by construction**, and the comment declares a link that does not exist. The day the cap goes up, the seventeenth who authenticates **at the same moment** receives `CREDENZIALI_ERRATE` — **indistinguishable from a wrong password** | `aiutante.c` · `rcp_autentica()` | ⚠ not today, ⛔ **on the day of the budget** |
| ⚠ **R10-A8** | **The findings folder is a single one and the file names are FIXED**, and the benches' grounds create it `1777` (one even `777` **without sticky**). ⇒ (a) tenant B can **read A's `cattura.bgrx`** — a raw frame of their desktop; (b) the second child fails the write and ⛔ **whoever diagnoses looks at the wrong desktop believing it is theirs** | `figlio.c` · `dichiara_priorita_audio()`, `:5595`, `:5051`; `banchi/07-b64-terreno.sh` | ⚠ **defect of the BENCHES**, not of the product — ⛔ but phase 10 runs ten users right there |
| ⚠ **R10-A9** | **A hostile tenant prevents another from opening the session with a `touch`**: the session log is `/tmp/remotix-sessione-<uid>.log`, `/tmp` is writable by everyone and the uid can be read from `/etc/passwd`. If the file exists and belongs to someone else, the redirection fails and the shell **exits before running the compositor** — ⛔ and the failure is **mute**, because `setsid --fork` exits `0` anyway | `sessione.c` · `avvia()` | ⚠ requires hostility, ⛔ cost of the attack: **one command**, effect **permanent and without symptom** |
| ⚠ **R10-A10** | **No cap on the number of QUIC connections**: `t->quante++` exists **only for the log line**. Thousands of connections that never send `CREDENZIALI` live 60 s each, **the ban never triggers** (no authentication fails), and the cost of the eleven scans of the list is paid by **everyone else's frames** | `trasporto.c` · `accetta()`, `webtransport.c` | ⚠ robustness |

### 4.3 ⭐ The ten leads **verified and discarded** — they are worth as much as the findings

⛔ In this project a lead closed with its reason written down tells whoever comes next that it has already
been looked at there. Line in hand:

1. ⛔⛔ **«Il secondo fisso mette dieci utenti in fila, l'ultimo aspetta dieci secondi» — IT IS FALSE**, and
   it is the most important lead to close. `RITARDO_FISSO` (`rcp.c` · `RITARDO_FISSO`) still exists and still applies
   to the admitted too, ⭐ **but it is not a wait**: it is a **per-session floor** checked in
   `rcp_tempo()` (`rcp.c` · `rcp_verdetto()`) with a clock comparison that **returns at once**. The wire never
   stops. ⇒ Ten users who come in together wait **one second each, in parallel**.
   ⚠ **The phase 1 sentence describes a product that no longer exists: it must be deleted, not
   re-verified.**
2. **The ban key with the port** — ✅ cured **by construction**: `rcp_chiave_indirizzo()` is
   the only one that builds the key, all three callers use it, and it is idempotent.
3. **The PAM helper as a bottleneck at ten** — ⛔ **false**: it is a dispatcher that **never
   calls PAM**, forks a grandchild per request, `SEQPACKET` socket. At 10 it holds with six slots
   to spare.
4. ⭐⭐ **Invariant I2 and the guardian's question** — ⛔ **the code asks the RIGHT question**:
   `sentinella.c` · `sentinella_locali()` discards the sessions **of other users** before looking at anything. The
   fear of `DECISIONI.md` §4.6-quater — *«c'è una sessione grafica locale?»* instead of *«…di questo
   utente?»* — **did not come true**. ⚠ The guardian's problem is not the question: it is the **multiplied
   cost** (R10-A3).
5. **The clipboard between tenants** — ⛔ **does not leak**: comparison on the user name session by
   session. Same for canvas, cursor, audio, input. No process-wide store: there was one, and it was removed.
6. **`MAX_POLL 64` leaving the children out** — count: 1 + 1 + 32 (page) + 1 (command) + 1
   (helper) + 16 (children, **only one per child**) = **52**, twelve of margin in the worst case, and
   the order is already the right one (the children at the end). ⚠ **Two readings that do not agree, and both
   are declared**: the design reading (§3.6 item 10) counted 36 and pointed out that the truncation of
   `figli_descrittori()` is **mute**. ⇒ They agree on the fact that **today it does not bite**; the finding that
   remains standing is not the number, it is that **if one day it bit, no line would say so**.
7. **Nested or quadratic loops on the number of sessions** — ⛔ **there are none**: all the scans
   are linear over tables of 8-256 entries with a body of one `strcmp`. The only cost that grows with N and
   is paid **per `poll` round** is not a loop: it is the D-Bus round trips of R10-A3.
8. ⭐ **The zero copy of phase 8 with ten tenants** — ⛔ **nothing shared in our
   code**: no `shm_open`, no `memfd_create`, no fixed name; the DMA-BUFs arrive from
   PipeWire **per user session**, and no `setrlimit` in the whole of `src/`. ⚠ What remains
   shared **is not ours**: the **encoding engine of the UHD 730 is one**, and ten VA-API contexts
   together are `[?]` — it is point 1 of the phase.
9. **The parent's resources fillable or readable by a tenant** — ✅ closed: command socket with
   `umask` **before** the `bind` and `0600` re-read via `stat`; certificates `0700` with the key `0600`;
   the child closes everything above 3; the ban file written with atomic `rename()`.
   ⛔ **The only two open are the findings (R10-A8) and the file in `/tmp` (R10-A9).**
10. **`presenti[16]` and `attaccate[16]` undersized** — ⛔ **not at 10**, and they degrade in a
    **declared** way.

### 4.4 The `[?]` of the lens

| `[?]` | why it stays open |
|---|---|
| **the real log at ten sessions** | the census is **static** (calls in the source), not a sample run with ten users. The structural conclusion does not depend on the sample; ⚠ the **exact fraction** does |
| **the cost of ten abandoned sessions** | `[M]` one costs **477 MB (PSS)** and ~0.017 % of a core (`main.c` · `consegna_verdetto()`). Ten would be ~4.8 GB **if it were linear** — ⛔ and it must not be assumed linear: ten `gnome-shell`s share pages. It is a number the phase must take |
| **the shared encoding engine** | no line of code governs it: there is nothing to refute by reading |
| **the real threshold of R10-A3** | how slow logind must be is arithmetic (`N × 300 ms` against 5000); ⚠ the real worst case of `ListSessions` with ten sessions open **is not measured** |

⛔ **And this lens left no bench**: it was read-only, it injected no faults, and
**boasts no healthy→fault→healed**. For the four findings that close with a measurement, the
measurement is named line by line.

---

## §5 · What was developed

> ⭐ **The third round, and the first in which `src/` is touched** — *25 Aug 2026*, on the director's order:
> *«prima applica le patch, poi scrivi il prodotto e dopo rifai i test»*.
> ⛔ **Every cure is tested with RED BEFORE and GREEN AFTER**, same scene and same bench, plus the
> **negative control** that puts the defect back and verifies that the bench **goes red again**.

### 5.1 ⭐⭐⭐ THE CHILD THAT DIED ON THE STRIDE — **and it was not the stride**

**The defect** (§6.8): with a window width that gives a DMA-BUF stride not a multiple of 64,
the child declares *«rimonto il palco sulla MEMORIA»* and **2 ms later dies of SIGSEGV**.

#### ⭐⭐ The line that fell — **read from the core, not deduced**

```
#0  ei_disconnect ()          da libei.so.1
#2  input_chiudi (…)          at input.c:1613
#3  smonta_il_palco (…)       at figlio.c:5897
#4  figlio_vive (…)           at figlio.c:7777
```

`[M]` And from the same core: `puntatore = NULL`, `tastiera_dev = NULL`, `regione_nota = 0` — the EIS
channel had been opened **33 ms earlier** and the `libei` handshake **had not arrived yet**.
⇒ ⛔⛔ **It is not the stride that kills: it is CLOSING A NEWBORN EIS CHANNEL.**

⭐ **And the proof the other way round**: `[M]` the same crooked canvas asked of a **mature** stage (20 s) ⇒ the
guard bites, the fallback mounts, **the child survives**.

#### The cure — **only the stream is remounted, not the whole stage**

Only `src/figlio.c` (+115 lines, −4): `rimonta_solo_la_cattura()` stops and reopens the `Cattura` **on the
same PipeWire node**, and redoes only the seam that lives there. `smonta_il_palco()` **remains as a fallback**
for the case in which the stream does not reopen.

⭐⭐ **It is the cure of the defect, not of the symptom**: the pixel route is a property **of the stream**, not
of the graphical session — the input channel, the clipboard and the `RemoteDesktop` session were being
thrown away **to change something that does not concern them**.
⛔ **The canvas was NOT aligned**: what the user sees **does not change** (no **I6**).

`[M]` **And it costs 500 times less**: the route change takes **2 ms** (4 measurements out of 4) against
**1 031 ms** for the full teardown — and the parent no longer receives *«il palco se n'è andato»*
⇒ **no `0x10` farewell**.

#### ⭐ Red before, green after

| | **pristine** binary | **cured** binary |
|---|---|---|
| view **1268** (stride 5072 ⛔) | ⛔ **dead 3 out of 3** | ⭐ **0 out of 3**, and *«vivo, desktop acceso»* 3 out of 3 |
| view 1280 (stride 5120 ✅) | 0 out of 3 | 0 out of 3 |

**And the delivery, counted** (new bench `10-c2-ripiego.py`, `--certifica` **27/27**):

| canvas | stride | outcome | fr. | bytes/fr | route |
|---|---|---|---|---|---|
| 1268×714 | 5072 ⛔ | ⭐ **deliver 3/3** | 10 | 2 743 | MEMORY |
| 1280×714 | 5120 ✅ | 3/3 | 11 | 2 780 | CARD |
| ⭐⭐ **854×480** — *the minimum of `SPECIFICHE.md` §5.5* | 3416 ⛔ | ⭐ **deliver 3/3** | 9 | 1 895 | MEMORY |

⭐ **The zero-copy guard bit 3 times out of 3**: the memory route **was really
travelled**, not bypassed.

**The negative control**: pristine file put back ⇒ ⛔ **1268: 0/2 deliver, 2 dead · 854×480:
0/2, 2 dead**. Cured one put back ⇒ green. ⭐ **Healthy → fault → healed, run.**
⭐⭐ **And the red added a fact that was in no document: 854×480 died too, the
declared minimum — nobody had ever taken it all the way to death.**

⇒ ⭐⭐ **The defect was ONE ONLY**: with the fallback cured, the zero-copy guard **stops being a
dead end and becomes a performance choice**, and `SPECIFICHE.md` §5.5 **stops promising a
canvas the product could not do**.

#### ⛔ And what the cure does NOT cure — declared, and outside the mandate

⛔⛔ **The real `libei` defect stays latent**: `input_chiudi()` calls `ei_disconnect()` **even on
a context that never completed the handshake**, and there `libei` falls. ⇒ The
**other two** `smonta_il_palco()` remain exposed — *«il palco se n'è andato»* and the exit one: **if the compositor
dies in the first tens of milliseconds of a stage's life, the same SIGSEGV comes back.**
`[?]` Not tested (it cannot be timed by hand). ⭐ The cure would be **a few lines in
`input.c`**: do not disconnect as long as no device has ever appeared.

⚠ Two more: the remount **presumes that the PipeWire node survives** the disconnection of the
consumer — `[M]` on Mutter **13 times out of 13**, even in ping-pong among three canvases, ⛔ but on another
compositor it might not hold (that is why the full fallback stayed) · and on the route change
**no keyframe is forced**: correct, measured, ⚠ **but it is a new behaviour** compared with before.

⚠ **And a declaration of honesty about the ground**: `[M]` the servers of three other assignments were alive
during the campaign. ⭐ The quantities reported are **counts** (deaths, frames, bytes) and a latency
of 2 ms, not GPU rates; and the red ↔ green flipped **with the binary, not with the load** — the
negative control ran with **more** neighbours than the green, not fewer.

### 5.2 ⭐⭐⭐ THE LOG NOW SAYS WHOSE IT IS — **from 4.4 % to 100 %**

**The defect** (§4.2 R10-A4, §6.7): with more than one tenant the log — *the tool with which every
defect of phase 9 and phase 10 was found* — **stops saying whom it is talking about**.

#### ⭐⭐ Red before, green after, and the negative control — **three binaries, same scene**

`[M]` Four real GNOME sessions of four different users, different scenes, 1080p, under the lock.
Bench `10-b96-registro.py` **reused, not rewritten**.

| | **RED** | ⭐ **GREEN** | **NEGATIVE** (defect put back) |
|---|---|---|---|
| attributable **overall** | 25.3 % | ⭐ **75.8 %** | 25.4 % |
| ⛔ attributable **DIAGNOSTIC** | **4.4 %** | ⭐⭐ **100.0 %** (20 277 out of 20 277) | **4.4 %** |
| ⛔⛔ **blind test** — I switch off a scene, I ask who stopped | seen 2/4 · **names 0 out of 4** | ⭐⭐ seen 4/4 · **names 4 out of 4, all RIGHT** | seen 3/4 · **names 0 out of 4** |
| ambiguous lines | 0 | 0 | 0 |

⭐ **The red reproduces §6.7 almost digit for digit** (there: 25.3 % · 4.2 % · 0 names out of 4).

The three families §6.7 measured at **0.0 %** — `fotogramma-spedito` (18 179 lines, **the most
voluminous of the product**), `ciclo-cattura`, `audio-blocchi` — all go to **100.0 %**.

```
07:29:41.112 rcp     fotogramma 214 SPEDITO: delta 1920x1080, codec 3, …
07:30:12.167 rcp     [provadec4] fotogramma 214 SPEDITO: delta 1920x1080, codec 3, …
07:30:12.398 figlio  [provadec6] ciclo: 1108 fotogrammi consegnati (0 chiavi), 12 attese a vuoto
```

**The cost, measured instead of predicted** (§6.7 predicted +7.8 %): `[M]` **+5.4 %** bytes per line,
⭐ **lines per second unchanged**. ⛔ **And atomicity holds**, which was the risk: `[M]` **0 orphaned and 0
interleaved** over 234 123 lines; the longest one carrying the identity is **822 bytes, 20 % of `PIPE_BUF`**.
⭐ And the detector **is not blind**: injecting some, it finds 4 out of 4.

#### What changed — **four files, and three of them for very few lines**

`registro.h` (+56) and `registro.c` (+79) carry the identity; ⚠ **`webtransport.c` only at lines
2116-2139** (the hook that threw away `ctx`), ⚠ **`figlio.c` only at 5953-5971** (the child that sets its
own name). ⛔ **`rcp.c` was NOT touched** — the identity arrives from the hook, and the twin copies
of R12.3 stay intact.

⭐⭐ **And a deviation from the assignment, declared and better**: instead of the **pid** the
**user name** was set. It costs the same, cures the same 359 lines **plus the 70 of `codificatore.c`**, and
⭐ **does not need the bridge** — which was the strongest argument of the finding (*rotated log ⇒ line
mute forever*). ⇒ The three caveats of §6.7 **close by themselves**: that `REG_CODIFICA` is the same
string as `REG_VIDEO` no longer matters, that the `figlio` area is written **by the parent too** no longer matters,
and the bridge is no longer needed.

⭐ And three detail choices that count: the bracket is composed **in one place only**, at the head of the
**body** and not between time and area (⇒ **an old reader keeps reading**); the identity is
**cleaned** (`]` and newline → `_`), because **a split line is plausible and false**; and ⛔ **whoever does not
know STAYS SILENT** — no bracket, no bytes.

#### ⚠ What the cure does NOT cure

⛔ **The 100 lines of `webtransport.c`** — `[M]` the family `wt stream uni … per un fotogramma`,
**18 211 lines**, stays at **0.0 %**. ⭐ The mechanism to cure it **already exists**: 76 in functions that already have
the context, 24 in the hooks. ⚠ It was left because that file belonged **to another assignment of the
same round** · the ten direct `fprintf(stderr,…)` stay mute (**none is diagnostic**) · the
**third-party** lines nobody touches · ⚠ **the format changes**: whoever reads by splitting into «ora · area ·
corpo» keeps working, whoever anchors on the body must tolerate `[nome] ` at the head.

#### ⭐ The five things nobody expected

1. ⛔⛔ **With the defect on, the log is WORSE than §6.7 said**: the blind test sees the
   fault **only 2 times out of 4** — it is not only mute, ⛔ **sometimes it does not even SHOW that someone
   stopped**. With the green: **4 out of 4**.
2. ⭐ The classifier that **guesses** goes from **96.5 %** wrong to **3.3 %** — not because
   it guesses better, ⭐ **but because it has almost no mute lines left to guess on**.
3. ⛔⛔ **The first round fell on the ground check, and the check was right**: it saw that the tree
   shipped **was not the one the bench was reading**. ⚠ **Without that predicate one would have
   measured the right binary while reading the wrong source.**
4. ⛔ The very first attempt started **in the second in which the previous bench was letting go of the lock and
   was still clearing** ⇒ *«il terreno non regge»* and *«non regge ANCORA»* **have the same
   face**. Cured with a breath and a retry.
5. ⭐ One family was **already** 100 % attributable even in the red, because **it names itself in the
   body** ⇒ ⚠ **the log was not mute: it was mute exactly where it was needed.**

⭐ **And the bench was improved where it was born crooked**: the predicate that *measured* the defect without
**judging it** now can give red on the cure; the final cleanup no longer uses **two global patterns**
(⛔ it was the fifth trap of §7.3, **written in the code**: it killed anyone else's clients); and
`--certifica` goes from 26 to **31 cases**, with the five new ones covering *wrong name ⇒ RED* and
*right name but diagnostics still at 4.2 % ⇒ RED all the same*.

---

### 5.3 ⭐⭐⭐ THE GUARDIAN CURED AT THE ROOT — and ⛔ **two evictions out of three did not reproduce**

`[M]` 25 Aug 2026, under the lock, ground **21 out of 21**. ⭐ **Two binaries built from the SAME
sources minus the cure**, swapped **without recompiling**, each with its declared `md5`.

#### ⭐⭐ P4 · The logind guardian — **from N calls to ONE**

The cell §6.13 had isolated: **N=7, D=286 ms**, that is *exactly the balance the code allows
itself*.

| arm | **calls per pass** | fps per session | p95 |
|---|---|---|---|
| red, D=0 | 7.5 | 30.20 | 66-84 ms |
| ⛔ **red, D=286** | **7.2** | ⛔ **1.45** | ⛔ **2 010-2 040 ms** |
| green, D=0 | ⭐ **1.07** | 26.99 | 74-104 ms |
| ⭐ **green, D=286** | ⭐ **1.07** | ⭐ **25.48** (−5.6 %) | 74-136 ms |
| ⛔ **negative control** | **7.24** | ⛔ **0.85** (−97 %) | **2 011-2 043 ms** |

⭐ §6.13 gave 1.3 fps with a p95 of two seconds: **found again** (1.45 and 0.85), and the cure brings it back to
**25.5 fps with 7 sessions out of 7 attached**.
⭐⭐ **And the column that proves the cure AT THE ROOT is the first**: one `ListSessions` answers for **all**
the tenants ⇒ **from N to 1**. It was the cure the numbers suggested (§6.13), and the numbers were right.

⚠ **And a predicate was REMOVED because it gave red on correct code**: the finding *«col guardiano lento
un inquilino nuovo non riesce a collegarsi»* **does not arise at D=286** — `[M]` the newcomer gets in within
**9 s** without the cure and **2 s** with it. §6.13 had seen it **at D=5 000**, which is another cell.

#### ⭐⭐ P2/P5 · *«il nostro silenzio contato come silenzio della rete»*

⭐⭐⭐ **And the line was already printing the proof that the network had nothing to do with it**: `persi=0` **and `cwnd_left=13200`** —
**the congestion window was wide**. ⇒ **There was room to send; we did not send because we were not
looping.**

| arm | outcome |
|---|---|
| ⛔ **before** | `linea-morta causa=stallo stallo_ms=12001 usciti_byte=0 persi=0 cwnd_left=13200` — on a session that **in the same cell was doing 40.36 fps**, ⛔ and **no line said why** |
| ⭐ **after** | ⭐ **zero evictions**; the guard arms **6 times**, worst gap **10 902 ms** |
| ⭐ **and it does not bite whom it should not** | 90 s of healthy machine ⇒ **zero** lines |
| ⛔ **negative control** | the eviction **comes back**, identical signature |
| ⭐⭐ **and the dead line STILL works** | `kill -9` on the client ⇒ **evicted all the same** in both binaries |

**The cure**: `wt_giro_del_padre()` + a declared budget — if more than that passes between two passes of the loop,
**the dead line does not judge that round and the counts restart**, with a line that says so.
⛔⭐ **And the piece of design that counts**: *a gap counts as **progress**, not as time to
subtract* — subtracting it would keep the clock behind forever, and **a client really dead would never
be recognised**.

⭐⭐ **And the eviction line now carries SEVEN new witnesses** (`fermo_ms=`, `giri_fermi=`,
`saltati=`, `ritmo_giu=`, `ritmo_arretrato=`, `ritmo_posti=`, `ritmo_scesi=`): §6.15 had to
**pair two lines by eye** to say *«il regolatore tratteneva»* — ⭐ **now the eviction line
says it.**

⭐ And `sentinella_conti()` **finally has a caller**: `[M]` with two sessions, `chiamate=29 → 59 →
89`, that is **30 per minute = one per pass**, `peggiore_ms=6`. And `LENTA_MS` drops from 20 to **10**,
because `[M]` at 20 **it would never have spoken**.

#### ⛔⛔ And the honest part: **two defects out of three did not reproduce**

| | |
|---|---|
| ⛔ **the loop of §6.15 did NOT reproduce** | `[M]` five saturated sessions, 150 s, **both binaries** → 37.6-38.1 fps each, latency 10-12 ms, **zero evictions**. ⇒ The bench says *«non giudico»*: ⭐ **«non si è presentato» non è «è curato»**. **P2 stays open**, and what the cure leaves is the **attribution**, so that the next reproduction says it in **one single line** |
| ⛔ **P5 in the form it was written does not reproduce** | `[M]` one session, **30 s of gap between two scenes** on a healthy loop ⇒ **no eviction**, `PING` every 5 s and answer within 1 s. ⇒ ⭐ **The «due volte» margin of §6.8 holds as long as the loop runs**: what breaks it is **the stopped loop, not the gap** |

⭐⭐ **And the unfair eviction can be COMMANDED**: `[M]` blocking the parent's loop reproduces it **3 times out of
3**, with identical signature — **without needing the saturated scene**. ⇒ That is the right scene to
measure it, and now it exists.

#### ⚠ The price, declared

⛔ **The P4 cure removes `N`, not `D`**: at N=7/D=286 a toll of **5.6 %** remains. Removing it means
moving the question **out** of the loop, onto a helper as was already done for PAM — **it is
another decision** · ⚠ **the guard costs a recognition delay**: a client that dies
*during* a gap is recognised up to one threshold later, and it is visible in `giri_fermi=` and
`saltati=` (`[M]` **zero** on a healthy machine).

`[?]` **The positive direction of invariant I2** (a real local session that wins over the remote one) was not
tested: on the machine **there is no session with a seat**, and creating one would mean
touching the user's desktop. ⭐ Mitigation: the two forms share **one single body**.

#### The injected faults — **44 out of 44**, and ⭐ **14 cases out of 44 end in «non giudico»**

lever not taken · zero calls · eviction with `persi=0` / without evictions / **with real loss** ·
log not read · guard that arms **under** threshold · guard that bites **a healthy machine** ·
calls per pass **in both directions** · rate that drops and that does not drop.

⚠ **Five bench defects found by running them**: the delay file with two different names
(⭐ **the «LA LEVA NON HA PRESO» guard saved two cells**) · the frame meter not calibrated ·
`ETXTBSY` copying over a running binary · `0x0F` instead of the handshake (slot not
yet freed) · ⛔ and **`scatti=None` becoming `[]`** — *«non ho letto»* turned into
*«zero»*, ⭐ **exactly the confusion all the predicates exist to avoid**, found by
`--certifica`.

⚠⚠ **And two declarations of honesty**: ⛔ `10-b97-guardiano.py` **still** carries a `pkill` with a
**global** pattern — the fifth trap of §7.3, **written in the code**, the one that already matched 24
live clients of another bench · and ⛔ **an isolation breach of our own, declared**: 1-2 tuning
sessions opened while the lock belonged to another assignment. ⭐ The scenes were off almost
always, **none of those numbers is reported**, and from then on we measured **only with the lock in
hand**.

---

### 5.4 ⭐⭐⭐ THE ELEVENTH NOW KNOWS — and the four `16`s have become **one**

`[M]` 25 Aug 2026, tree compiled with the cap at **2**, under the lock. ⭐ **And the bench verifies the
scene before judging**: *«palchi 2 su 2 (PIENI) e posti 1 su 2 (ce n'è uno LIBERO)»* — that is
exactly the defect: **the children table full while the slots table has room**.

| | ⛔ **RED** (yesterday's product) | ⭐ **GREEN** |
|---|---|---|
| on the wire, **read in the client** | ⛔⛔ **nothing**: `AMMESSO` · `SESSIONE` · *«ancora attaccato dopo 60,0 s: niente è caduto»* | ⭐ `CONGEDO invece di AMMESSO: motivo 0x0E` |
| pixels | ⛔ **no frame in 60 s** | the `AMMESSO` never arrives: **there is no black page to have** |
| how long it takes | ⛔ **61.6 s, and it never gets better** | ⭐ **0.6 s** |
| the body | — | *«i palchi di questo server sono tutti impegnati (2 su 2): sono sessioni grafiche vive, che si liberano al logout o dopo l'abbandono»* |
| ⛔ **the sentence the user READS** (real Firefox) | ⛔⛔ **«Ammesso, sessione nuova, tela 1188×714, desktop sconosciuto»** | *«quella sessione non si può servire»*, ⭐ byte-identical to the `0x0E` entry of the served file |
| desktop switched on for the rejected one | 0 `gnome-shell`, 4 processes | 0 `gnome-shell`, 4 processes |
| **verdict** | ⛔ **3 reds out of 8, 1 «non ho misurato»** | ⭐ **8 predicates, 0 reds, 0 «non ho misurato»** |

> #### ⛔⛔ And the worst thing was said by **the real browser**, and nobody had foreseen it
>
> The defect **is not** *«una pagina nera senza spiegazione»*. It is that the page writes **«Ammesso,
> sessione nuova, tela 1188×714»** — that is, ⛔ **it reassures the user**, and then never sends them a pixel,
> forever.
> ⭐ **A mute black makes them doubt; a «you are in» makes them wait.**

#### The four `16`s — and ⛔ **the fifth that stays separate, with the reason written**

⭐ One single number, `RCP_TETTO_SESSIONI` in `rcp.h`, with the box that lists the four places where it was
written by hand **and the three comments that declared a non-existent link**. Now following it are
`MAX_ATTACCATE` (`rcp.c`), `MAX_FIGLI` (`figlio.c` — ⭐ *the comment that said «lo seguirà dallo stesso
posto» is now true*), `QUANTI_PRESENTI` (`main.c`), and ⭐⭐ **`WT_PALCHI`, which rises from 8 with them**:
it bit at **nine**, that is **before the promised ten**.
⛔ **And `MAX_IN_VOLO` stays 16 and stays SEPARATE**, with the box that explains why: it is **another
quantity** — the authentications *in flight*, which are counted even **with zero sessions**.

⭐ And the **mute** `return` of `presenza_segna()` becomes a **declared fallback**, one single line and not
one per gesture (`CODER.md` §4.2).

⭐⭐ **And the proof of the `#define`s is read AFTER THE PREPROCESSOR**, not in the sources: *looking at how they are
written is the wrong question*, and it is the error that comment had been making for months.

#### ⭐ Why `0x0E` and not `0x06` — the reason, next to the line

`0x06 BUDGET_PIENO` says *«questa macchina non ha più capacità di codifica»*: a **physical** limit.
Here the limit is **a table full of stages nobody is watching** — **administrative**, which is
what `0x0E` already says. ⇒ **D5**: the two reasons **add up**, and `0x06` belongs to the budget round.

⚠ **And the page's sentence would deserve different words, but not these**: `0x0E` now covers **five**
cases, and making it precise for one would make it **false** for the other four. ⭐ The new case however is
**the only one of the five that has a gesture and a time** — the user can ask a colleague to log out, and
in any case it gets better at abandonment. ⛔ **It is a decision for the director.**

#### The negative control — **four faults injected and run, plus 38 off-field**

`congedo-muto` ⇒ ⛔ **3 reds out of 8** (it is the red of the table) · `figli-slegati` ⇒ ⛔ `v[16]` against
`attaccate[2]`, **the red of §6.4 reproduced** · `palchi-otto` ⇒ `palchi[8]` · `presenti-slegati` ⇒
`presenti[16]` · **healed** ⇒ ⭐ all at 2, and `volo[16]`.
And off-field `--certifica`: **38 out of 38**, of which **5 meter calibrations that run in the real
round too**, and ⛔ *«il fiato vuoto non è uno zero»* · ⚠ *«RESPINTO ⇒ non ho misurato, mai respinto
correttamente»*.

#### ⛔⛔ And three consequences that concern everyone

1. ⛔⛔ **The cure BREAKS the ground of `10-b93`**, and **in the worst way**: that script runs `sed` on a
   `#define` that **no longer exists**, the `sed` exits **0 without substituting**, the ground **declares
   success**, the cap stays 16, and the bench ends in *«non ho misurato»*. ⭐ **The cure is one line**,
   and it must be done before redoing the tests.
2. ⛔ **`POSTO_NIENTE_PIU_POSTI` is no longer reachable by a new user**: slots full ⇒ children
   full, and the no arrives **earlier**. ⇒ The cure of **R9.3**, seen triggering for the first time in §6.4,
   **becomes practically unobservable** — the branch stays as a net. ⭐ **And it is D6 coming true**:
   `[M]` the rejected one has **0 `gnome-shell` and 4 processes**, against the **42 processes and 1 `gnome-shell`**
   of §6.4.
3. ⛔⛔ **Shared users steal each other's password, and EVERYONE's ban pays for it**: `[M]` the
   first round died with a user **rejected for credentials** on a password set half an hour earlier
   — `07-b64-terreno.sh utente` **rewrites it at every call**, and the last one to call wins.
   ⛔⛔ **And every rejected one consumes one of the three attempts of the ban by ADDRESS, which lasts twelve hours and
   puts every other agent out of action.** ⇒ ⭐ **The real cure belongs to coordination**, not to the bench: that
   script must not redo the password of a user that already exists.

⚠ **What the cure does NOT cure**: ⛔ **it is not the budget** — the cap stays a `#define`, and this round makes it
**possible** (one single number instead of four copies) · ⛔ **the declared price**: whoever passes
PAM and has no stage receives `0x0E`, whoever gets the password wrong `0x07` ⇒ **the reason says that the password was
right**. It is the same price the code already pays today, ⭐ **and it is the cost of not leaving the user
in front of a black screen**.
`[?]` `WT_PALCHI` from 8 to 16 **was not tested with nine users**: here it is correct **by construction**,
not measured.

---

### 5.5 ⛔⛔ THE LENS ON THE STITCHING — **the product holds, the BENCHES do not**

*25 Aug 2026, adversarial read-only mandate. The thesis to refute was mine:* ⛔ *«le quattro
cure sono state cucite senza conflitti e l'albero compila ⇒ vanno bene insieme»*.

⭐ **The first half holds**: in the **product** there is no crossing that kills — **thirteen leads
verified and discarded**, line by line (the doubled `WT_PALCHI` against the loops that walk it ·
the log hook called with the session already freed · the pointers held across the
farewells in the batch · the new `#include` that pulls in a symbol · the identity that survives the
remount · invariant **I4** · `presenti[]` overflowing · and the types of the seven new fields).

⛔⛔ **The second half is FALSE, and in the worst direction: the cures broke each other IN THE BENCHES.**
⇒ *«It compiles» was not «it works together», nor even «it can still be measured».*

| # | the finding | how much |
|---|---|---|
| **R1** | ⛔⛔⛔ **The log cure breaks the frame meter of FIVE benches**, and ⛔ **the zero that comes out of it ACCUSES the product**: `resa()` with zero matches **does not return `None`, it returns 0** — and its own comment says that zero on a live scene *«è un GUASTO»*. ⇒ The bench reports that the server **did not send a pixel** while it was sending them all. It is the rule *«`None` non è zero»* **broken from the inside**, and it touches **point 1 of the phase** | ⛔⛔⛔ |
| **R2** | ⛔ `10-b2-terreno.sh` has **the same dead `sed`** already cured in `10-b93` — ⛔ and its guard is **blind in the permissive direction**: it looks for the old string, does not find it, **and therefore does NOT give red**, going on to measure *«tabella piena»* on a table of sixteen | ⛔⛔ |
| **R3** | `i_due_numeri()` of `10-b93` is **mute forever** — *«una tabella da None»* — ⛔ **and `--certifica` stays GREEN**, because it injects the dictionaries by hand. **Green instrument, measurement off** | ⛔ |
| **R4** | ⛔ **None of the new lines of the loop cure carries the name**: 93 mute calls against **one single** that names. ⇒ **The «4.4 % → 100 %» was measured on a tree that did not contain the other cure**, and ⛔ **the eviction line — the most important of phase 9 — is among the mute ones** | ⛔ |
| **R5** | ⛔ `fermo_ms=` in the eviction line is the **GLOBAL** counter while the comment next to it says *«da quando questa sessione è nata»*. ⇒ On a server running for a day, an eviction after ten seconds would say `fermo_ms=40000`: whoever reads it **acquits the network when the network was involved** — ⭐ **the INVERSE error of the one the cure exists to remove** | ⛔ |
| **R6** | A **second** branch become unreachable besides the one already declared: *«N figli già vivi»* will never come out again | ⚠ observability |
| **R7** | Two new comments that **lie**: one says a line is written by `main.c` (⛔ nobody writes it: if one day the wrong hook is connected, **the pass switches off without a line**), the other promises in the line the **number of tenants**, which ⛔ **is not there** — and it is precisely the denominator needed to **reject** the cure | ⚠ |
| **R8** | ⛔ **`WT_RIPASSO_INSIEME 32` is the FIFTH hand copy**, born **in the round that unified four of them**, and its comment ties itself to *«i sedici posti»* — **a literal, not the `#define`** | ⚠ today, ⛔ **on the day of the budget** |
| **R9** | The cure of the loop gap **also** resets the **stall** clock ⇒ on a machine on which the loop exceeds the budget more often than once every five seconds, ⛔ **neither stall nor silence ever triggers**: the dead line **stops existing**. ⭐ It is not silent (`saltati=` grows), ⛔ but **no predicate looks at that number**, and the price was measured at 1, 2, 5 and 7 sessions — **never at ten** | ⚠ |

#### ⭐ What was cured at once, and by whom

**R1** — the five patterns now read **both line forms** (the identity group is
**optional**), and ⭐⭐ **the meter was given the guard that would have caught it by itself**: the
**raw** occurrences of the word in the text are counted, and if there are some but the pattern takes
**none**, the bench **refuses to report zero** and says it is the meter that is broken.
⇒ *A real zero and a dead-pattern zero have the same face: the only way to tell them apart is to
look at the text with coarser eyes.*

**R2** and **R3** — cured in two places (by the coordination and by whoever was measuring), with the `sed` that
now **counts whether it bit** and the reader that reads **the single number** keeping the reading of the two
names **as a check**.

**R4**, **R5**, **R7**, **R8** stay **open and assigned**: they are product cures, and this round
**tests, it does not cure**.

#### ⛔ And two defects of the shared grounds, found while measuring

1. ⛔⛔ **`accendi` exited ZERO on a DEAD server**: `[M]` with an option the binary does not know,
   the server prints its own help and exits, and the ground said *«OK server 1265806 sulla porta
   8260»* **exiting 0**, with the unit already `inactive` and **no listener**. ⇒ A bench that
   trusted it would say «on», then «the table does not fill», and ⛔ **would end up accusing the
   product of a defect that was a non-existent option**. ⭐ Cured: *«acceso»* now means
   **that someone is listening**, and if nobody listens the lines that say why are printed.
2. ⚠ **`RIFAI_PAROLA` did not cross the `ssh`**: the morning's cure — *do not redo the password of a
   user that already exists* — had been put in the half that runs **on the server**, but the variable was not
   in the list passed to it. ⇒ **It did nothing, silently.** Cured.

#### ⭐ And a question closed **by reading**, which is worth writing down

⛔ **`POSTO_NIENTE_PIU_POSTI` is no longer reachable by any route.** The new user is stopped
**before** the `ATTACCA`; and the route of the dying child does not get there, because the death goes through
`wt_congeda_utente` → `congeda` → `posto_lascia`, which **frees the slot in step**.
⇒ ⭐ **The cure of R9.3, seen triggering for the FIRST time in §6.4, goes back to being unobservable** —
⚠ **but this time because the no arrives earlier and better**: the two branches stay as a **net**.

---

### 5.6 ⭐⭐⭐⭐ THE ELEVEN REAL DESKTOPS ON THE STITCHED TREE — **the four cures cost nothing**

`[M]` 25 Aug 2026, tree with the **four cures stitched**, eleven real users, steps of 45 s at
steady state, ⭐ **ground 21 out of 21 before EVERY scene**.

#### ⭐⭐ The anchor finds the SIX again — so the numbers can be compared

`[M]` `capienza = 6`, cliff **at the eighth** (29.63 → 1.85 fps), and the bench declares it by itself.

| | **still** (11) | ⭐ **real** (11) | **saturated** (6) | **saturated** (11) |
|---|---|---|---|---|
| fps each | 0.02 · *(0.02)* | **9.67** · *(9.79)* | 38.62 · *(38.54)* | 0.98 · *(0.97)* |
| median latency | 15.1 ms | ⭐ **8.0 ms** · *(8.0)* | 11.3 · *(11.2)* | 1 121.7 · *(1 134.7)* |
| GPU **render** | ⭐ **0.0 %** · *(0.0)* | 22.2 % · *(22.3)* | 88.2 % · *(88.8)* | 99.5 % · *(99.6)* |
| GPU **VEBOX** | 0.0 % | ⚠ **23.9 %** · *(24.1)* | 51.6 % · *(52.6)* | 0.9 % |
| total PSS | 2 031.8 MiB · *(2 028)* | 3 374.9 · *(3 382)* | 1 262.4 · *(1 257)* | 2 208.5 · *(2 209)* |
| violations of **I1** | 0 | ⭐ **0** · *(0)* | 0 | ⛔ **38** · *(37)* |

*(in brackets the numbers of §6.12, **before** the cures)* ⇒ ⭐⭐ **every column matches within 1-3 %.**

#### The four questions, with the answer

1. ⭐ **Does the real desktop hold eleven without a scratch: yes.** `[M]` the first session goes from 10.43 to
   **9.55** fps from the first to the eleventh — **−8.4 %**, under the tolerance (§6.12: −7.7 %) — with
   **zero violations of I1, zero not judged**, **flat** latency (8.6 → 8.5 ms) and zero keyframes.
2. ⭐⭐ **Eleven STILL desktops still cost zero GPU**: `[M]` 0.0 % on all four engines at
   every step, **RC6 100 %, GT 0 MHz**. ⇒ ⭐ **The budget design does not need redoing.**
3. ⭐ **The log costs what it declares, and less than was feared**: `[M]` **445.6 lines/s ·
   58.7 kB/s · 131.7 bytes/line**, and ⭐⭐ **the cost per line does NOT grow with the number of tenants**
   (115.8 → 119.6 bytes/line from 1 to 7 sessions; the lines/s grow **linearly**). ⇒ Rate and latency
   **are not affected**.
   ⭐⭐ **And the attribution HOLDS at eleven**: `[M]` diagnostic lines **100.0 %**, **11 distinct names out of
   11**, **0 ambiguous lines**, and ⛔ **atomicity holds: 0 orphaned, 0 interleaved, 0 truncated over 524 552
   lines**, the longest **823 bytes** — identical to the 822 measured at four sessions.
4. ⚠ **The cliff has not moved**: `[M]` **870.65 Mpixel/s redrawn hold, 991.44 collapse**, and the
   line gives the ceiling at **846.3** against the ~842 of §6.12 — ⭐ **0.5 % deviation**, and inside the
   873-953 of §6.15.

#### ⭐ The cures seen working, one by one

- **the guardian** — `[M]` **30-31 calls per minute, that is ONE per pass, identical from 1 to 11
  sessions** and **even inside the collapse**. `giri_fermi=0`, `giro_peggiore_ms=0`. ⭐ Before the cure
  it would have been `N × D`.
- **the loop** — ⭐ `[M]` **zero unfair evictions in 27 minutes**, including **five minutes of collapse at
  1 fps with 1.1 s of latency**. The 22 `linea-morta` lines of the round fall **all** in the two instants
  in which the bench kills the clients. ⇒ ⭐ **The dead line is not unconditional and can still bite.**
- **the cap** — at eleven: `posti occupati 11 · negati 0`, correct. ⛔ **The cure was not
  stressed**: seventeen users would be needed.
- **the stride fallback** — ⛔ **not stressed**: the canvases are 1920×1080, stride a multiple of 64.
  `[M]` **zero SIGSEGV**, and the 44 child deaths of the round are **all signal 15**, that is the clearing.

#### ⛔ The four things nobody expected

1. ⛔⛔ **The CPU column of §6.12 is almost never ours.** `[M]` at saturated with eleven the machine reads
   **15.1 %**, but the bench's server costs **0.01 cores** and its clients **0.01**. At the first «vero»
   step the machine is at **1.7 %**, at the first «satura» at **9.3 %**, **with the same own load**.
   ⇒ ⛔ **The lower CPUs of this round are not a merit of the cures: they are the other tenants of the
   test machine.** ⚠ *Whoever compares that column between two rounds is comparing the traffic of the
   other benches.*
2. ⛔ **The hole of `webtransport.c` declared in §5.2 is a QUARTER of the whole log**: `[M]`
   **73 091 lines out of 299 709**, at **0.0 %** attribution. ⇒ **It is not a tail: it is the second
   family by volume**, and at eleven sessions it **stays mute**.
3. ⭐ **The VEBOX overtakes the render engine on the stitched tree too** (23.9 % against 22.2 %) — ⛔ **and the
   VEBOXes are ONE**, the VDBOXes two. It confirms §6.12 for the **second** time.
4. ⚠⚠ **The lock was taken by breaking into the previous one by ONE SECOND**: `[M]` the other's expiry
   fell at 11:14:53, the racer won at **11:14:54** after 6 689 rounds. ⭐ Before measuring
   it was verified that **no `remotix` was alive and no port listening**. ⛔ **But it is the sixth
   trap of §7.3 seen from the other side, and it was a hair**: a turn underestimated by two seconds
   would have made us measure **on top of** whoever was there.

#### The `[?]`

⛔ **The blind test at eleven sessions** was not done: the bench carries a **fixed list of
four** sessions, and extending it would mean **touching a certified bench in a round whose rule
is «non si cura niente»**. ⭐ What can be said with the number is **the mechanism on which the blind test
rests**: attribution **100.0 %** and **11 names out of 11**, against the 4.2 % and **0 names out of 4** of §6.7 ·
⛔ **the ceiling of the real desktop**: at eleven the GPU sits at 22-24 % — **the users ran out, not the
machine** · ⛔ **the real network**: the clients run on the same machine · ⚠ the **+5.4 %** bytes per
line **was not re-measured**: a second tree without the cure would be needed.

⚠ **And a declared isolation breach, which is still in the code**: `10-b92-dieci.py` carries in its
`finally` a `pkill` with a **global pattern** — ⛔ **the fifth trap of §7.3, written in the code**.
It matched nobody **only because we always ran with the lock in hand**.

---

### 5.7 ⭐⭐⭐⭐⭐ THE BUDGET — **the product stops accepting everyone and starving everyone together**

`[M]` 25 Aug 2026, **saturated** scene 1920×1080 H.264, steps of 30 s, eleven real users, under the
lock, ⭐ **ground 21 out of 21 at every arm**.

| step | ⛔ **RED** — budget off | ⭐ **GREEN** — `--budget-mpixel-s 480 --riserva 0.5` |
|---|---|---|
| 6 | 472.5 Mpx/s · 37.98 fps · I1 reds **0** | 478.7 Mpx/s · **38.47 fps** · I1 reds **0** |
| 7 | 396.0 Mpx/s · **27.28** fps · ⛔ **I1 reds 6** | ⛔⭐ **`CONGEDO 0x06 BUDGET_PIENO`** |
| 8 | 35.3 Mpx/s · ⛔ **2.12 fps** | ⭐ **does not exist** |
| `0x06` emitted | **0** | **1** |
| bench verdict | 8 steps · ⛔ **28 reds** | 7 steps · ⭐ **1 red** (the budget's no) |

⭐ **And the line that said it carries the numbers**:

> *««provamt7» ha superato PAM ma NON entra: le **6 sessioni già aperte ne chiedono 496 dei 480
> Mpixel/s dichiarati**, e la tua ne chiederebbe altri 82 (1920×1080 a 39,5 fot/s)»*

⇒ ⭐⭐ **The child is not born** (**D6**), and the no goes out **on the wire**.

#### The four checks, all run

| | |
|---|---|
| ⛔ **the negative control** | budget switched off again, same scene ⇒ **8 steps · 26 reds**, `2,14 fot/s` at the eighth, `0x06 = 0`. ⭐ **The red comes back** |
| ⭐⭐ **the test that counts double** | **ten STILL sessions with the budget on ⇒ ZERO refused**. *A budget that refused ten tenants who cost nothing would be as wrong as one that admits the eighth* |
| ⭐ **the positive control, and it costs 30 s** | budget at **40** Mpx/s, **below the cost of one single** 1080p ⇒ **the FIRST is refused**, `0x06` on the wire, **zero processes switched on** |
| ⭐ **the meter calibrated FIRST** | the real module mounted and compared with the certified predictor: ⭐ **8 scenes out of 8 match**, and it finds the numbers of §6.9 again **by construction** — the sixth saturated gets in and the seventh does not · the tenth still one gets in and the eleventh does not · at eight throttled the count on pixels would say *«c'è posto»* (328 ≤ 484.8) and ⛔ **the latency gate refuses** at 654 ms. Two negative controls bite: the knob in both directions, and **off never denies** |

#### ⭐⭐ The thing nobody expected, and it is the reason it works

`[M]` At the **sixth** step the budget counts **496** Mpixel/s while the machine delivers **478.7**.
⛔ **It is not an error**: it is **the reserve at work**. The counted demand is an **upper bound** of the
delivered, ⇒ ⭐⭐ **and it is precisely that margin that makes the no fall on the SEVENTH instead of
on the eighth — that is, BEFORE the cliff instead of inside it.**

#### What changed

`src/budget.h` + `src/budget.c` (**new**) · in `main.c` the capacity question **in front of**
`figli_assicura()` and the accumulation **inside** `deposita_fotogramma()` — ⭐ **without guards, so it sees
the ghosts too** · the three options and the startup lines · `rcp.h`/`rcp.c` the accessors and
`attaccate[]` **allocated**, with the default going down **from 16 to 10** · `figlio.c`, `webtransport.c` and
`main.c` with the other three tables **allocated** · `registro.h` the new area · the R12.3 twins
aligned.
⇒ ⭐ **The four `#define`s unified by the previous cure become a CONFIGURABLE cap**, which was
the debt with the written deadline.

**The bench contract written beforehand is respected in all five points**: the option names
· the startup line in the log **on and off** · `0x06` with the body **and the figures** · `0x06 ≠ 0x0E` ·
the `negati` at every verdict **even with the budget off**.

#### ⛔ The defect the budget unmasked in the sentence, and its cure

**«Rimpicciolisci la finestra» was FALSE at the gate.** The `0x06` is decided **before the
stage is born**, and there the only canvas number in hand is `video.misura_massima`, which is the ceiling of the
client's **DECODER** — not of the window (`pagina.html` · `VIA_MSE()` spells it out, and `:1608`
measures it with `VideoDecoder.isConfigSupported`). ⇒ ⛔ **Whoever shrank and retried received the
very same no.**
⭐ The currency stays the **pixel** — never the heads, which are the other branch — ⛔ **but the lever is the
DEVICE, not the window**.
✅ **Cured**: the sentence now says the only true thing, that is **when the capacity comes back**.

#### The `[?]` and the bench defects

`[?]` **`--tetto-sessioni` is verified only in the startup line** (asked 7 → in force 7): the four
tables follow it **by construction**, it was not taken to the ceiling with seven users ·
`[?]` **the latency threshold has never bitten on its own**: the count on pixels always decided ·
`[?]` **the buffer lead does not cross the process border** — that number lives in the child, and
here there is only the measurement.

⛔ **Four bench defects, three not its own**: ⛔ an `exec` on a **non-executable** script killed
the first campaign **after** it had already taken and released the lock (**an hour lost**; `[M]` 146
bench scripts were without `+x`, all cured) · a division by zero in the summary of a **still**
scene · three grounds that run `sed` on a `#define` that is now 10 — ⭐ **and the cure is not
fixing the `sed`, it is REMOVING it**: `--tetto-sessioni N` does **at runtime** what they did by
recompiling · ⛔ **and one is its own, declared**: the summary prints «uscita 1» for all five
arms, and the five `1`s **mean different things** — useless as a judgement, and the real numbers
must be read from the tables.

---

## §6 · The measurements

### 6.1 ⭐⭐ THE GPU METER — calibrated, and with a discovery that changes the budget

`banchi/10-b87-metro-gpu.py`, `[M]` 24 Aug 2026, i5-13500T / UHD 730 / `renderD128`, with the lock
taken.

**The route that works**: `/proc/<pid>/fdinfo/<fd>` on `i915`. `[M]` The keys that kernel
**really** exposes — looked at in the file, not in the documentation: `drm-driver`, `drm-client-id`,
`drm-pdev`, `drm-total-*`, `drm-engine-render`, `drm-engine-copy`, **`drm-engine-video`** (cumulative
ns), `drm-engine-video-enhance`, **`drm-engine-capacity-video: 2`**.
⛔ `/sys/class/drm/card*/clients` **does not exist** on this kernel.

⚠ **The VDBOXes are TWO**: the maximum of `drm-engine-video` is **200 %**, not 100. ⛔ Whoever confuses
*«engine-equivalents»* with *«fraction of the capacity»* gets the budget wrong by **a factor of two**.

#### The calibration — the reading follows the exposure

`[M]` `h264_vaapi` `EncSliceLP`, raw nv12 in a loop, 12 s of measurement after 4 s of warm-up, **two
independent rounds**:

| known load | Mpx/s **arrived** | video % read | expected | deviation |
|---|---|---|---|---|
| zero (twice) | 0 | **0.00 / 0.00** | 0 | — |
| 1 × 1080p30 | 62.21 (100 % of what was asked) | **12.68 / 12.69** | ref. | — |
| 1 × 1080p**15** (half rate) | 31.10 | **6.63 / 6.67** | 6.34 | +4.6 % / +5.1 % |
| 2 × 1080p30 | 124.42 | **24.59 / 24.51** | 25.36 | −3.1 % / −3.4 % |
| 4 × 1080p30 | 248.83 | **49.96 / 49.59** | 50.74 | −1.5 % / −2.2 % |
| 1 × 720p30 | 27.65 | **6.43 / 6.82** | 5.64 | +14 % / +21 % |

⭐ Doubling and quadrupling the load the number doubles and quadruples; at half rate it gives ~half.
Line: `video_pct = 0,1968 · Mpx/s + 0,68`, root mean square error **0.47 points**. Repeatability
±0.6 %.

#### ⛔⛔⛔ And the discovery, which is the most important of the phase

**`drm-engine-video` measures BUSY TIME, not WORK DONE** — and the time depends on the frequency
of the GT, which the governor moves **with the load**.

`[M]` Exactly the same encoding, 1080p30, **30.00 frames/s delivered in both cases**:

| GT locked at | video % |
|---|---|
| **300 MHz** | **26.41** |
| **1550 MHz** | **7.01** |

⇒ **work equal within 0.0 %, occupancy different by a factor of 3.77.**

⛔⛔ **Consequence: the line `k` does NOT extrapolate.** The `k = 0,204 % per Mpx/s` measured at light
load would give *«un motore saturo a 490 Mpx/s, la capacità video a 981»* — and it is a **lower bound
wrong by up to a factor of ~4**, because at light load the GT stays low and every frame
takes more time. At 1550 MHz locked the same count would give ~890 per engine, ~1780 in all.

⭐⭐ **Hence the rule for the whole phase: the real number of the encoder is measured at SATURATION,
it is not drawn from a line.** Whoever uses this meter to estimate capacity must **either saturate, or
lock the GT and declare it**.

⇒ Every reading now carries next to it the **GT context** (requested/min/max frequency, with «⚠ BLOCCATA» if
min = max) and the **RC6 residency** — ⭐ a **second measurement independent** of the `fdinfo`s
(100 − RC6 = upper bound on the card's occupancy), which confirms the phenomenon: `[M]` **28.9 %
awake at 300 MHz against 9.9 % at 1550 MHz**, same load.

#### The injected faults

`--certifica`: **43 out of 43** green, on the laptop and on the test machine as root. `fdinfo` denied
(**live** injection, on 35 real clients) · key missing · pid dead between the two readings · counter
going backwards · `drm-client-id` changed · impossible jump (3000 %) · recycled pid · `dt = 0`,
`dt < 0`, `dt = 50 ms` · the kernel writing *«abc ns»* · one of the two readings missing · RC6
going backwards. ⛔ **In every case `None`, never zero, never a huge number, never negative.**

⭐ **And the red was really seen**, with two negative controls: breaking the meter (guard on `dt`
removed, «not measured» → 0) the certification drops to **25/36** with `ZeroDivisionError` and
a `video_pct = −100 %`; removing the guard «found but none readable» it drops to **34/36**.

⚠ **To see the whole machine root is needed**: as a normal user `gnome-shell` cannot be read and the
total comes out marked `[?] parziale — limite inferiore`, **not 0**.

#### The `[?]` of the meter

**the saturation point** — 4 × 1080p30 are only **25 %** of the video capacity: the knee
was not looked for, and it belongs to the saturator · **whether `drm-engine-video` separates encoding from decoding** —
it is the VDBOX, it does both · **the render cost of real capture** — here `drm-engine-render`
stayed at 0.00-0.05 % because the source went through the CPU.

⭐ **And an isolation note the meter declares instead of deducing**: while A1 was measuring the servers
of three other benches were alive. `[M]` In the two «zero» scenes the machine total is **0.00 %**, and in
all the others it coincides **exactly** with the sum of its `ffmpeg`s. ⇒ No other DRM client
occupied the video engine: the lock held.

*(to be filled in along the way)*

### 6.2 ⭐⭐⭐ THE NUMBER OF THE ENCODER — **`renderD128` sustains 1.86 Gpixel/s in H.264**

`banchi/10-b88-saturatore.py` (+ `10-b88-flusso.c`, `10-b88-costruisci.sh`, `10-b88-sonda.py`,
`10-b88-esiti.jsonl`), `[M]` 24 Aug 2026, **59 rounds**.

**The scene of every row**: i5-13500T (20 threads) · Intel UHD 730 `renderD128` (`i915`, iHD 25.2.3),
the Radeon closed off by udev · `h264_vaapi` · ⭐ **`EncSliceLP` verified on the driver**, not just requested ·
QP 26 · bframes 0 · zero copy (DMA-BUF from GBM) · ground `10-b0` **21 out of 21 green** · ⚠ scene
`testsrc2`, ⛔ **not a real desktop: the rate counts, the Mbit/s do not**.
⚠⚠ **And the codec premise was corrected by §6.10**: this ramp is in **H.264**, which the first
round believed to be *«quel che il prodotto negozia davvero»* — ⛔ **the product negotiates HEVC first**
(`rcp.c` · `prima_comune()`, `pagina.html` · `inquadra()`), and in HEVC the ceiling is **2.33 Gpixel/s**, **+25 %**.
⭐ And the isolation **measured, not assumed**: while it ran, the servers of four other benches
were alive on the machine — `[M]` **the strangers on the video engine were `0,0 %` in all 59 rounds**.

#### The brick, measured **twice independently**

| where it gives way | Mpixel/s | video engines | GT | median latency |
|---|---|---|---|---|
| 1080p30, N=32 | **1855.9** | **99.5 %** (199.1 out of 200) | 1350 MHz, RC6 0 % | 561 ms |
| 4K60, N=4 | **1865.8** | **99.7 %** (199.4 out of 200) | 1350 MHz, RC6 0 % | 486 ms |

⭐⭐ **The ceiling does not depend on the canvas: it is the engine.** And the two VDBOXes **both fill up**
(199 out of 200) — there is no *«one engine full and the other idle»* defect, which the bench was able to
recognise.

#### ⛔ The table of `SPECIFICHE.md` §5.5 goes from `[?]` to `[M]` — **and all three rows were wrong, by DEFECT**

| 10 sessions at… | the document said | ⭐ **measured** |
|---|---|---|
| **480p · 25** | ~100 Mpixel/s · «una cinquantina» | **103.9 Mpixel/s** at **5.5 %** of the engines. ⛔ «una cinquantina» is **wrong by defect**: 32 streams hold (332.6 Mpixel/s, 17.8 %) and the scale stopped at the **bench's ceiling**, not the hardware's. By pixels the ceiling is at **~180 sessions** |
| **1080p · 30** | ~620 Mpixel/s · «giusto al limite» | **623.1 Mpixel/s** ✅ the number is right, ⛔ **but it is not the limit: it is 33.2 %.** **24** hold (1494.7 Mpixel/s, 79.7 %) |
| **4K · 60** | ~5 Gpixel/s · «una sola» | ⛔ **5 Gpixel/s do not exist**: the ceiling is **1.86**. **TWO** hold (995.5 Mpixel/s, 52.1 %), not one |

**Cost per frame** (median, N=1): 480p **0.86 ms** · 1080p **3.00 ms** · 4K **9.18 ms** — that is
2.10 / 1.45 / 1.11 ms per Mpixel: ⭐ **the large frame costs less per pixel**.

#### ⛔⛔ Why it gives way: **the GPU**, with the proof next to it

In all three give-ways the attributed cause is the **GPU**, with the number: video engines ≥ 99.5 % of
capacity, GT at 1350 MHz, **RC6 0 %** (never asleep). ⛔ **The CPU was never the bottleneck**:
**1.2 cores out of 20** at the breaking point on the card route. No software fallback,
no re-encoding, no frame held back, memory never near the limit.

> #### ⇒ ⛔⛔ **Q1 and Q2 are BOTH REFUTED**
>
> **Q1** said the measured ceiling would be **lower** than the table: it is **higher**, and
> on all three rows. Ten sessions at 1080p30 are not *«giusto al limite»*: they are **a third**
> of the hardware.
>
> **Q2** said that what gives way first would **not** be the GPU, but memory or CPU: ⛔ **it is the GPU**,
> in all three cases, with the CPU at 1.2 cores out of 20.
>
> ⭐ It is the result that shifts the phase: **the constraint of this machine is the encoding engine, and at
> ten sessions it is not even close.** ⚠ And it remains to be seen what happens when behind every
> stream there is **a real GNOME desktop** instead of `testsrc2` — it is the bench of the ten.

#### ⭐ The five things nobody expected

1. ⛔⛔ **The minimum canvas of `SPECIFICHE.md` §5.5 CANNOT use zero copy.** `[M]` 854×480 → the
   GBM buffer comes out with stride **3416**, which **is not a multiple of 64**: the guard of `codificatore.h`
   refuses the import. ⇒ **The product's minimum necessarily goes through the memory route.**
   (The 480p were measured at **864**×480, stride 3456, declaring it.)
2. **The memory route** (`sws_scale` + `av_hwframe_transfer_data`): it had been concluded that
   it gave way on the GPU like zero copy, with a real CPU cost to put in the budget. ⚠ The measurement
   no longer holds after phase 18 (the conversion is now ours).
3. ⭐⭐ **The long round does not change the rate, it changes the LATENCY.** 15 s and 60 s give the same
   Mpixel/s at the tenth (1855.9 → 1856.0), ⛔ but the median latency goes from **561 to 2317 ms**
   (worst 1061 → 4505): **beyond the ceiling the backlog grows with the exposure.** It is
   `LEZIONI.md` §1.32 applied to the right quantity.
4. **Colour conversion is a SECOND GPU consumer** the budget must count: at
   saturation `drm-engine-video-enhance` sits at **70 %** while video is at 99.5 %.
5. ⚠ **Our path pays ~20 % of rate for latency**: `[M]` free `ffmpeg`, one 1080p
   stream = **406.2/s (842 Mpixel/s)**; the product, which waits for the packet right after the `send`,
   would do ~333. ⭐ **It is a choice, not a defect — but now it has a number.**

#### The injected faults — **7 out of 7 as expected**

healthy (2 streams 1080p60) GREEN · **G1** stream that does not start (`renderD127`) ⇒ RED *«NON È PARTITO»*,
and ⛔ **not counted as 0 fps** · **G2** software fallback (`libx264`) ⇒ RED *«RIPIEGO IN
SOFTWARE»* · **G3** count read **from the previous round** (nonce) ⇒ RED *«è il conteggio di UN
ALTRO GIRO»* · **G4** rate not kept ⇒ RED *«chiesti 60/s, arrivati **41,4**/s»*, **with the number,
not rounded** · **G5** GPU meter blind ⇒ occupancy `[?] non letta`, **never 0 %**, and the
GPU cause *«non si può né affermare né escludere»* · healed GREEN, and ⭐ **healthy ≠ healed**
(14.9878 against 14.9879 s: two real rounds, not the same one read twice).

#### The `[?]` of the saturator

⛔ **HEVC was not run**: **only H.264** measured, as assigned — the bench can do it
(`--codec hevc`), and the two columns would stay **separate, not averaged** · ⛔ **the absolute value**:
the GT at saturation sits at **1350 MHz out of 1550 declared**, so there is some margin and it **is not
quantified** (it is the §CLOCK of §6.1) · ⚠ the meter declares every reading **partial** — 1 process not
inspectable out of ~1400 ⇒ the occupancies are a **lower bound** · ⛔ **synthetic scene** · the
480p ceiling was not reached: the scale stopped at N=32 **by choice**.

### 6.3 ⭐⭐ THE NETWORK BUDGET — and ⚠ **two phase 9 cures that fight each other, but only for the test client**

`banchi/10-b90-filo.py` (+ `10-b90-getto.c`, `10-b90-sessione.sh`), `[M]` 24 Aug 2026, 2560×1080,
**H.264**, phase 9 cures **on**, under the GPU lock.

#### The meter is exact, not «close»

`[M]` Jet at **5 · 20 · 60 Mbit/s** (12× range) → deviation on the bytes **+0.0000 %** on all
three, slope **1.000000**, constant **0**. The accounts close with a zero balance:
`interfaccia = mio + tara + ICMP + vicini`. ⚠ It counts the **IP length** (verified: 1000 B of payload
= 1028 B) ⇒ it includes QUIC headers, ACKs, retransmissions and audio; **not** the ethernet frame —
the datagrams are 1467-1472 B, so **on the copper +2.6 %**.

#### The numbers

| scene, 30 s | mean on the wire | peak | **×10** | frames | bytes/fr |
|---|---|---|---|---|---|
| **still** | **0.0029** Mbit/s | 0.010 | **0.03** | 1 | 316 |
| **real desktop** | **0.531** | 0.756 | **5.3** | 673 | 2 099 |
| **hard** | **4.478** | 21.9 | **44.8** | 907 | 16 884 |

⭐ The payload of the real desktop is 0.374 Mbit/s ⇒ **the wire costs +42 % of the video**: *the budget
is made on the wire, not on the video*.

⛔ **And the ceiling is NOT the constraint**: `enp7s0` negotiates **10 000 Mbit/s** (read from `/sys`; `ethtool` is not
there), and bare UDP on `lo` does **11.9 Gbit/s with one single thread**, 72.6 with eight. `[?]` How much **encrypted**
QUIC can sustain is not measured.

> #### ⇒ ⛔ **Prediction Q9 is REFUTED**
>
> It said the network budget would bite **before** the GPU one. `[M]` Ten sessions on the hard
> case make **44.8 Mbit/s** on a 10 Gbit/s card: **0.45 % of the wire**. ⭐ The wire is not the
> constraint of this machine.
>
> ✅ **THE DISCREPANCY IS RESOLVED IN §6.14, and in two stages**: `[M]` the **44.6 of phase 9 was TRUE** —
> re-measured today it gives 46.9, that is **6 %** deviation — and the two «scene dure» **were not the same
> thing**: the phase 9 one was **pure noise**, which compresses **five times worse**.
> ⚠ **And a factor of 2.2 belongs to this measurement**: `[M]` the same scene re-measured gives **9.647 Mbit/s and
> 37 420 bytes/frame** against the 4.478 and 16 884 here. ⇒ **The number to look at with suspicion is
> the one of this section**; ⭐ the conclusion — *«il filo non è il vincolo»* — **does not change**.

#### ⭐⭐⭐ And the still scene costs **992 times less** — the audio cure of phase 9

`[M]` Phase 9 §14.2 gave **2.427** Mbit/s with a still screen; here it does **0.0024**. With the cure switched off
(`--niente-audio-silenzio`): **2.4275 Mbit/s**, that is the 2.427 of phase 9 **found again to the third digit**.
⇒ Ten still sessions: **0.024 Mbit/s today against 24.3 before**.

#### ⛔⛔⛔ And the line the product writes by itself: **the two cures fight each other**

```
linea-morta causa=silenzio silenzio_ms=10004 prove=16 persi=0 permille=0
```

`[M]` On a **still** desktop, on `lo`, with **zero** loss, the session is **closed after 10 s**.
With only the audio cure switched off, the same still session **survives the whole 30 s** (6060
packets).

⇒ ⛔ **The audio cure removed the traffic that kept the client answering, and the dead line —
calibrated when that traffic was there — evicts whoever has nothing more to say.** *«Mai staccare»* is
the only obligation that holds everywhere, and here what triggers it is not a bad network: it is **another cure
of the same product**.

> #### ✅⭐⭐ CLOSED BY THE REAL BROWSER — and the finding SHRINKS, without disappearing
>
> `[M]` §6.8: on **real Firefox 140 ESR**, still desktop, cures at defaults, the session
> **survives** at 120 s and at 300 s, and `causa=silenzio` **never triggers**. ⇒ ⛔ **The defect belongs to the
> test client, not to the user.**
>
> ⚠ **But it is not an acquittal, and it is the part not to lose**: what keeps the line alive **is not the
> browser** — `[M]` **29 packets out of 29 from the client are ANSWERS, zero spontaneous** — it is **the
> `PING`s of our transport**, sent at **half** the silence threshold. ⇒ ⭐ **The cure holds
> because the server asks**, and the margin is **twice**: if that interval rose above the
> threshold, the defect would come back **on browsers too**.

#### The contention — who pays, when the wire is narrow

`[M]` 60 Mbit/s on port 8020 alone, hard scene, cures on:

| sessions that were sending | total | per session | threshold | abandonments | keyframes | rate down/up |
|---|---|---|---|---|---|---|
| 1 | 9.19 | 9.10 | 0 | 0 | 0 | 2/2 |
| 1 (2 requested) | 24.09 | 23.88 | 0 | 0 | 0 | 5/5 |
| **2** (3 requested) | **48.61** | **27.30 · 20.89** | **8** | **8** | **8** | **38/38** |

⭐ With **one** session **no cure triggers**. With **two**, the total reaches **81 % of the wire** and
**all** of them trigger — ⛔ and **no line says that the problem is the neighbour**. And the split is not
fair: **+31 % to whoever arrived first**.

⇒ ⭐ **Q5 is confirmed in substance and corrected in the mechanism**: the sessions *see each other
as a bad network* — but what detaches is not the regulator (which brakes itself, and that is fine), it is the
**dead line**, and by the route of **silence**, not of the stall.

`[?]` It was not possible to keep **three** video sessions alive together: the dead line evicts them
before the player paints.

#### The injected faults

healthy → fault → healed: **7 → 12 → 6**, all **run**. Counter read before the stream ·
`nft` zeroed · interface going backwards · two readings at the same instant · 2 frames in 10 s
with log not read · a session lost from the set · `nft` rule lost · `mbit()` with `None`,
0 s, negative seconds. ⭐ **And two real reds in the field**: an arm at zero bytes refused, and the
guard that declared *«2 su 3»* instead of calling it n=3.

⚠ **The bench defects paid for and cured along the way** (all of the shape *«silence instead of red»*,
`LEZIONI.md` §1.29): `wc -l < file` at the end of `sudo -S` → silent `None` · `awk`'s `$1` expanded
by `bash -c` → empty field · `nft` braces taken by bash for a command group · `ss -uanp` that
**does not see** the ports of `aioquic` (unconnected socket) · the ICMP *«port unreachable»* at 576 B
per datagram, which without its own counter ended up under **«vicini»**.

⛔ And an isolation cure that holds for the whole phase: `banchi/10-b90-sessione.sh` closes **only its
own** sessions — `09-b71` closed with `pkill -f 01-b3-cliente.py`, which in phase 10
**would kill the neighbours' clients**.

### 6.4 ⭐⭐ THE FULL TABLE — the cure of **R9.3 seen triggering for the first time**

`banchi/10-b93-pieno.py` (+ `10-b93-terreno.sh`, `10-b93-lancia.sh`), `[M]` 24 Aug 2026,
1920×1080, H.264, clean line, under the lock.

⚠ **The trick is declared**: tree compiled with **`MAX_ATTACCATE=2`** (the `sed` on **both**
twin copies, or the Makefile refuses — R12.3), ⛔ the repository's `src/` **not touched**, and the
number **read from the binary at runtime**: *«il registro delle sessioni di questo server e' PIENO (2 su
2)»*. ⇒ What is measured is **the behaviour on filling up**, not the number.

| # | question | measurement |
|---|---|---|
| 1 | **the reason on the wire** | ⭐ **`CONGEDO 0x0E` in 10 out of 10**, never `0x0F`. **The cure of R9.3 was seen triggering for the first time** |
| 2 | **the detail in the body** | present 10 out of 10: *«il registro delle sessioni di questo server e' pieno»* |
| 3 | **the PAGE's sentence** | **real** Firefox 140 ESR: *«quella sessione non si può servire»*, byte-identical to the `0x0E` entry of the served page ⇒ built from that reason. It goes back to the login form. ⚠ **Generic, not false** |
| 4 | ⭐ **does whoever was inside get worse?** | **NO.** `provadec4` 37.82 → **39.23** → 37.38 fps; worst second 33 → 35 → 32; p95 35 → 36 → 35 ms; ⛔ **keyframes 0/0/0**; gaps 0. `provadec5` 38.36 → **39.88** → 37.34. Anchors of the two clocks agreeing within **68 ms** and **54 ms** |
| 5 | **leftovers, over 10 refusals** | slots taken by the rejected one **0** · children **3 fixed** · gnome of the rejected one **1 fixed** · fds **14 fixed** · RSS **+6 kB per refusal** · processes of the rejected one 15 → 42 → **41 fixed** (the step is the first session finishing switching on, not a leak) |
| 6 | ⛔⛔ **where the border falls** | **authenticated YES · child BORN YES · graphical session ON YES** · stage delivering a frame no. ⛔ At the end of the round `provadec6`, **never admitted**, had **42 processes and 1 `gnome-shell`** — like the two that got in |
| 7 | **does the slot come back?** | **clean** close: **1.48 s** · ⛔ **sudden** death (`-9`): **10.111 s** for the slot to become free again, **11.69 s** for the rejected one to be inside |

> ⇒ ⭐ **Q8 is confirmed, and worse than it was written**: it is not *«rifiutare dopo aver acceso un
> desktop»* — it is that **the desktop is switched on even for someone who will never be admitted**.
> ⇒ ⭐ **Q7 confirmed**: `MAX_FIGLI` **does not follow** `MAX_ATTACCATE` — 2 against 16, and with the two
> diverging the slots table fills up at 2 while the children table still accepts **14**,
> which are born **for users who will be rejected**.
> ⇒ ⛔ **Q4 is refuted in this scene**: whoever was inside **does not get worse**, and does not get worse even
> on the mechanism column (keyframes 0/0/0). ⚠ **But the scene is two sessions with the table
> filled artificially**: the GPU is not under strain. The prediction stays open for the climb to ten.

⚠ **And point 7 corrects phase 9**: what frees the slot **is not the 30 s of `SILENZIO` §5.3** — it is
the **dead line** (`silenzio_ms=10111 soglia_silenzio_ms=10000`), on by default since 24
Aug. And the eviction of §4.4 has nothing to do with it: it applies only between clients of the **same** user, and whoever waits is
someone else.

#### ⛔⛔ The red nobody was looking for: **the second route of §3.1 does not start**

`[M]` Over 10 refusals: **10 closes ARMED, 0 capsules queued.** The client **never** saw
a session close code, and the QUIC connection ends with **0** — which `RCP.md` §3.1 says
*«NON DEVE essere usato»*.

⭐ **The mechanism has a name**: `chiudi_sessione()` **delays the capsule by 500 ms**
(`WT_ATTESA_CHIUSURA_NS`, and it is the cure of **B11**, put there so that a browser would not throw away the
`CONGEDO`), and a client that detaches as soon as it has read the `CONGEDO` leaves **~2 ms later**.
⇒ **Only one route remains**, and it is precisely the one v1 had already lost for three phases.

> #### ✅⛔ WITHDRAWN BY THE REAL BROWSER — *«0 capsule»* was true **for `aioquic`**
>
> `[M]` §6.8: with **real Firefox** as the rejected one, the capsule **arrives 10 times out of 10**, with code
> **`0x0E`** and **never `0`**, at **0.593 s** from the farewell — and the server log says **armed 10,
> sent 10**.
> ⇒ ⭐ **The second route of §3.1 is not broken: it is invisible to clients that detach at once.** The
> test client leaves ~2 ms after the `CONGEDO`, that is **498 ms before** the capsule starts.
> ⛔ **And the lesson is about method, not about the product**: that finding had been taken by reading **where the
> capsule leaves** instead of **where it arrives**.

#### ⭐ The design that comes out of it: `0x06` **adds to** `0x0E`, it does not replace it

| reason | what limit it is | the gesture the user can make |
|---|---|---|
| **`0x0E`** | **administrative** — the table is full. ⭐ And it is right today, because the number is a `#define`, not a measured capacity | *«il server ha già tutte le sessioni che può tenere: riprova, o chiedi di alzare il tetto»* |
| **`0x06`** | **physical** — the encoder cannot cope | *«questa macchina non ha più capacità di codifica: riprova, o entra chiedendo meno qualità»* — ⭐ and the second is **a gesture, not a consolation** |

⚠ The sentence of `0x0E` **stays generic**, and for a reason: `0x0E` already covers **three** cases in `rcp.c`;
making it precise for one would make it **false** for the other two.
⛔ **And the piece the design must carry along**: the budget must be asked **before the
child is born**, that is in `consegna_verdetto()`. Deciding it at `ATTACCA` means **refusing when the
budget has already been spent**.

#### The injected faults — **45 tests, 45 did what they had to**

Meter calibration, which runs **in the real round too**: the channel reader finds a known `CONGEDO`
again · the chopper finds known rates again (40/12/40) · the anchor refuses a polluted «before» ·
the offset between the two clocks is found again, is **refused** if the two anchors diverge by 1 s, and is
**declared unverified** if there is only one anchor.
Faults: `0x0F` on the wire · empty body · ⛔ **wrong password / banned / server off ⇒ «non ho
misurato», never «respinto correttamente»** · rate collapsing · **gap of 2 s with the mean rate
intact** (the worst second catches it) · ⭐ **keyframes rising with the rate intact** (§1.31) ·
offset not measured · one extra child at every refusal · slot never freed · refusal after the desktop ·
slot that does not come back or comes back late · the two numbers diverging · page that lies, is mute, is not
looked at · code 0 · the two routes contradicting each other · **armed 10 sent 0**. Every red
healed right afterwards.

⚠ **The bench defects paid for along the way**: `registro_da()` with the `tail` at the end **lost the `posto
PRESO`** under thousands of lines · the scene switched off **before** the clients shifted the second anchor
by **42 s** · `pgrep -f` counted **7** children where there were 3 (the ssh, the sudo and two bashes **that
were asking**) and then **0**, because the child renames itself with `prctl` and `comm` stays «remotix» ·
⛔ **`pkill -f` killing the shell that is running it**, because the pattern is in its `argv`: the
cleanup did not happen and **the next test started against ghosts**.

### 6.4-bis ⭐⭐ HOW MUCH **ONE** SESSION COSTS — and the memory estimate was wrong by **six times**

`banchi/10-b89-costo-sessione.py` (+ `10-b89-agente.py`, `10-b89-scena.sh`, `10-b89-terreno.sh`),
`[M]` 24 Aug 2026, port 8010, `provadec1`, 1920×1080, **one** real RCP session on real headless GNOME,
40 s per scene after 12 s of settling (⭐ **the steady state is measured**), under the lock.

⭐ **Meter calibrated first**: two VA-API 1080p encodings at **15 and 30 fps** — known ratio **2.00**,
the meter says **2.00** (deviation **0 %**).

| | **still** | **real desktop** | **continuous motion** |
|---|---|---|---|
| frames delivered | **1** in 40.8 s | **774** (18.92/s) | **1 711** (41.77/s) |
| **bytes per frame** | 266 | **5 130** (max 8 978) | 1 805 (max 4 354) |
| Mpixel/s | 0.05 | 39.2 | **86.6** |
| wake-up pixel → bytes out | n/a | **median 10.0 ms · p95 10.5** (25 tears out of 25) | n/a |
| **child** memory PSS | 29.4 MB | 29.8 | 29.8 |
| **graphics** memory PSS (RSS) | 169 (664) | **301 (1 019)** | 201 (796) |
| CPU (machine) | 0.13 % | 0.44 % | 1.23 % |
| GPU **rendering** | **0.00 %** | 3.24 % | **10.01 %** |
| GPU **encoding** (VDBOX, ×2) | 0.01 % | 3.26 % | 8.83 % |
| GPU **enhancement** (VEBOX, ×1) | 0.00 % | 3.70 % | **10.55 %** |
| GT mean / awake | **0 MHz / 0 %** | 265 MHz / 11.3 % | 208 MHz / 30.3 % |

#### ⭐ And the ×10 — **a prediction, not a result**

| | still | real desktop | continuous |
|---|---|---|---|
| **memory** | **1.82-1.95 GB** out of 31 | **2.96-3.25 GB** | 2.06-2.26 |
| Mpixel/s | 0.5 | 392 | **866** |
| Mbit/s | 0.02 | 8.3 | 8.4 |
| CPU | 1.3 % | 4.4 % | 12.3 % |
| GPU rendering / VEBOX / VDBOX | 0/0/0 % | 32/37/16 % | **100 / 106 / 44 %** |

⛔ **The order of who runs out first**: **enhancement (VEBOX) 106 % > rendering 100 % > encoding 44 %
> CPU 12 % > memory 7 % > wire 3 %.**
⭐⭐ **A prediction taken from ONE ALONE, and confirmed by the climb to ten of §6.5, which measured it**:
the bottleneck is the GPU, and **it is not the encoder**. ⚠ The GPU column is an **upper bound** (§CLOCK of
§6.1: the GT sat at 208-265 MHz out of 1550) — the real value lies between that number and that number divided by
~4.

#### ⭐ The five things nobody expected

1. ⭐⭐ **The estimate of `DECISIONI.md` §4.6 is wrong by SIX times, and in the comfortable direction**: it said
   *«dieci sessioni GNOME ferme sono ~12 GB dei 31»*; `[M]` they are **1.8-1.9 GB** — and even ten **whole**
   RSS would make 6.6 GB. ⇒ **Memory is not the bottleneck, and does not even come close.**
2. ⭐⭐ **The bottleneck is not the encoder**, which is the hypothesis on which §4.6 builds the whole budget: it is
   the compositor's **rendering** and above all the **VEBOX**, which costs **more** than the encoding
   engine (10.55 % against 8.83 %) ⛔ **and is ONE ONLY**, while the VDBOXes are **two**.
3. ⭐ **A still session costs ZERO GPU, literally**: RC6 at 100 %, GT at **0 MHz**, one
   frame in 40 s, 2 kbit/s on the wire.
4. ⭐ **The «desktop vero» costs more than the «caso peggiore»** in two quantities out of four: 301 MB of graphics
   PSS against 201, and **5 130 bytes per frame against 1 805**. ⇒ **Two real windows weigh more
   than a synthetic scene at full rate** — and it is lesson §1.30 from the other end.
5. ⛔⭐ **`REVIEWER.md` E15 reproduced live**: the first threshold was on **bytes per frame**, and
   `[M]` the **healthy** scene makes 1 651-1 805 of them against the **1 982** of the same scene **frozen**
   ⇒ that quantity **orders the two extremes backwards**, and no threshold could separate them. The
   quantity that separates them is the **rate** (44.6/s against **0.55/s**). ⚠ It is the wound of `LEZIONI.md`
   §1.33, found again on another quantity.

#### The injected faults — **16 out of 16**

the session does not open ⇒ *«IL SERVER NON È ATTIVO: non misuro»*, **not** «0 fotogrammi, regolare» ·
orphan stage found **before** measuring · memory reader without permissions ⇒ **`None`, not
zero**, ⭐ **and the multiplication by ten refuses itself** · «continuo» that does not move, unmasked
by the **rate** · GPU reader without permissions ⇒ no GPU column.
⚠ **And G1 is injected by switching off the server, not with a wrong password**: that would trigger the
ban by address, which lasts 12 hours and **starts from the same address as every other agent**.

#### The `[?]`

⛔ **The worst case in BYTES is not answered here**: none of these scenes has real entropy (the
colour bands compress very well) ⇒ 8.4 Mbit/s for ten against the 44.6 of phase 9. It is the
job of §6.3 · the **latency** on «ferma» and «continuo»: the wake-up meter lives on the tears,
and on the other two the **cadence** is reported, which is another quantity · the absolute of the GPU (§CLOCK).

### 6.5 ⭐⭐⭐⭐ THE TEN REAL ONES — **SIX fit**, and the bottleneck **is not the encoder**

`banchi/10-b91-terreno-dieci.sh` + `banchi/10-b92-dieci.py`, `[M]` 24 Aug 2026. Scene **`pieno`**
(it saturates the encoder, as written in `PIANO.md`), 1080p, H.264, steps of **45 s at steady state**,
eleven real users with real GNOME desktops, one single server on 8100, under the lock.

⭐ `[M]` **One at a time they all arrive**: 11 out of 11 at `SESSIONE`, 1894-2075 ms.

| sessions | fps each | median latency | GPU **render** | GPU video | CPU | PSS | wire |
|---|---|---|---|---|---|---|---|
| 1 | 39.6 | 9.9 ms | `[?]` | `[?]` | 5.5 % | 287 MiB | 2.2 Mbit/s |
| 2-5 | 37.7-38.5 | 9.2-10.3 ms | 28.9 → 73.3 % | 8 → 21 % | 8.5 → 14 % | 483 → 1062 MiB | 4.2 → 10.3 |
| ⭐ **6** | **38.0-39.4** | **10.6-14.8 ms** | **88.8 %** | 27 % | 18.9 % | 1252 MiB | **13.1** |
| ⚠ **7** | **23.5-29.1** | **39-47 ms** | **99.1 %** | 22.9 % | 17.6 % | 1443 MiB | 10.7 |
| ⛔ **8** | **1.45-1.72** | **408-761 ms** | **99.5 %** | 1.6 % | 14.7 % | 1633 MiB | 0.69 |
| ⛔ 9 / 10 / 11 | ~1.2 / ~1.07 / **0.95** | 875 / 1025 / **1143 ms** | 99.5 % | 1.2 % | ~15 % | 1824/2014/2203 MiB | ~0.6 |

- ⭐ **Six saturated sessions fit together**: all at ~38 fps, ~10 ms, 5.6 kB per frame (⭐ **the
  scene bites**, §1.30), zero gaps, zero keyframes.
- ⚠ **The seventh breaks everyone**: −28 % of rate for those already there, latency **×4**.
- ⛔ **The eighth is the cliff**: **1.5 fps for everyone**, half a second of latency. There is no recovering from there.

> #### ⛔⛔⛔ AND THE PREMISE OF THE PHASE IS REFUTED: **the bottleneck is the `render` engine, not the encoder**
>
> `DECISIONI.md` §4.6 says: *«il limite vero lo pone il codificatore, e si misura in pixel al
> secondo»*. `[M]` **On this hardware it is not true**: the **video** engine (the two VDBOXes) **never passes
> 27 %** of capacity; the **`render`** engine goes to **99.5 %** and stays there.
> ⇒ **The bottleneck is compositing and colour conversion, not encoding.**
>
> ⭐ **And the two benches do not contradict each other: they measure two different quantities** (`LEZIONI.md` §1.28).
> The saturator (§6.2) was fed `testsrc2` — **no compositor behind** — and found the
> ceiling of the **encoder**: 1.86 Gpixel/s. Here behind every stream there is **a real GNOME desktop
> that composites**, and the machine stops at six sessions ≈ **370 Mpixel/s**, that is **20 %** of that
> ceiling. ⛔ **Both are right, and the number that governs the product is the second.**

**The other three quantities are not the bottleneck**: CPU max **18.9 % out of 20 cores** · memory **linear,
~190 MiB PSS per session** · wire **13.1 Mbit/s in all**.
⭐ `[M]` **PSS 2203 MiB against 7452 MiB of summed RSS** at eleven sessions — **factor 3.4**:
summing the RSS would have said *«sette giga e mezzo»*.
`[M]` **Opening the nth session does not get worse with the number**: 1926-3264 ms, and the eleventh
opens in **2021 ms while the machine is on its knees**.
`[M]` **Network budget**: **2.19 Mbit/s per saturated session** ⇒ ten are ~22 Mbit/s, **7 %** of the
300 declared. ⭐ **It confirms §6.3 by another route: the wire is not the problem.**
`[M]` **Two durations** (§1.32): 45 s and 90 s at the same step give **0.96 and 0.95** fps ⇒ the collapse
is **a stable state**, not a drift that accumulates.

#### The three questions of the phase, with the answer

1. **Do ten fit?** ⛔ **No: SIX.** It degrades at the seventh, collapses at the eighth, and the resource that
   runs out is **the GPU, `render` engine**. ⇒ ⛔ **Q3 refuted.**
2. **Does whoever was already inside get worse?** ⛔⛔ **Yes, and catastrophically**: `s1` goes from **39.60 to 0.96
   fps — minus 97.6 %** — when the eleventh arrives. `DECISIONI.md` §4.6-bis and invariant **I1**
   are **violated for every session at every step from the seventh up**: `[M]` **104 paired reds**.
   ⭐ **The product has no budget: it accepts everyone and starves everyone together.** ⇒ ⭐ **Q4 confirmed**,
   and in the worst way.
3. **The eleventh?** ⛔ It gets in **without problems**: `posti occupati 11`, **`negati 0`**, and receives **0.94
   fps with 1170 ms of latency**, leaving the other ten at the same level.

#### ⭐ The four things nobody expected

1. ⭐⭐ **The bottleneck is the `render`.** The whole phase was set up on *«budget di pixel del
   codificatore»*: **the encoder sits at 27 %**.
2. ⭐⭐ **The keyframe spiral NEVER switches on** — `[M]` **0 keyframes out of 8741 frames**, even in the
   collapse. ⚠ `LEZIONI.md` §1.31 says to carry the mechanism next to the symptom: **here the mechanism
   is silent**, and the degradation goes by **another route** — the **latency**, which goes from 10 ms to 1.2 s.
   ⇒ The column that warns **is not always the same**: in phase 9 it was the keyframes, here it is the latency.
3. ⛔ **There is no soft knee**: between the sixth and the eighth one goes from 38 to 1.5 fps.
   **It is not degradation, it is a cliff** — and the phase 9 degradation ladder does not soften it.
4. ⛔ **Nine defects were in the bench, not in the product — and eight out of nine WERE SILENT** instead of giving
   red (`REVIEWER.md` **E14**, `LEZIONI.md` §1.29): `pgrep -f` finding itself (⇒ every session
   would have resulted «alive» forever) · path from outside instead of from inside the container · the
   `lo` counter **that was not its own** (22× bigger than the real one) · the `barra` scene that **did not
   bite** · `drm-engine-capacity-video: 2` read **as nanoseconds**, with a ceiling of 100 instead of 200
   · the GPU delta over a **changing population of contexts** (occupancy **−76 %**) · `misura()`
   overestimating the fps by 1/(N−1) · the seven `enable-linger` processes mistaken for an orphan stage.

⭐ **And two of those nine were avoided by the calibrated meter of §6.1**: the capacity **2** and the lesson of the
§CLOCK. Without that file the GPU budget would have been reported **wrong by a factor of two**.

#### The injected faults — **42 cases, 0 reds**, each healthy → fault → healed

Session that does not open (⛔ **the climb stops**, it does not count nine) · anchor that does not advance · client
dead ⇒ `None` not zero, **and the mean of the living does not drop** · orphan stage unmasked **before**
measuring · same `numero` in two steps ⇒ red · ten still screens **unmasked by the bytes** ·
keyframe spiral the rate does not see · **I1 in the three outcomes** (healthy / violated / not attributable to
saturated CPU) · GPU meter: double count, discrete card, capacity 2, dead context, negative
occupancy, zero while frames pass · clients as bottleneck · latency calibrated with **5 / 40 / 137 ms
injected** · *«non ho letto»* ≠ zero.

#### The `[?]` of the ten

⛔ **The real network**: the clients run on the same machine, on `lo` (MTU 65536) ⇒ the network budget
is **counted, not tested** · ⛔ **the image**: the bench does not say *«si vede peggio»*, and that is said by
the user · the GPU at the first step, cancelled by the sixth bench defect · **the «attese a vuoto» per
session**: `figlio.c` · `figlio_vive()` does not say **which child** the line belongs to, and with ten children they can only be read
as a sum (⭐ it is finding R10-A4 of §4.2, found again from the other end) · **the average desktop**: the scene
saturates on purpose; the light case is worth `[M]` 2 448 B/frame and 0.77 Mbit/s.

### 6.6 ⭐⭐⭐ THE STUDY OF THE HARDWARE — and ⭐ **colour conversion runs on the EUs**

`banchi/10-b94-ferro-vaapi.py` (talks to `libva.so.2` with `ctypes`, ⚠ **there is no compiler on the
test machine**) + `10-b94-ferro-carico.py` (engine meter via the **PMU of `i915`**,
`perf_event_open` in `ctypes`) + `10-b94-lancia.sh`. `[M]` 24 Aug 2026, under the lock.

#### What the driver declares, and how one verifies that it obeyed

`[M]` iHD 25.2.3, libva 1.22: the only encoding entrypoint is **`EncSliceLP`, for all codecs**
(§4.6 confirmed). H.264 High: CBR · VBR · CQP · MB · QVBR · TCBRC, ⛔ **no ICQ, VCM, AVBR**;
maximum size **4096×4096**; `l1=0` ⇒ **no B**. HEVC Main10: the same plus **VCM**, size up
to **16384×12288**, `l1=3`.

⭐ **The driver does NOT substitute**: `[M]` `vaCreateConfig` **refuses 13 modes out of 13** not offered, with
`VA_STATUS_ERROR_INVALID_VALUE`. It is what `LEZIONI.md` §1.8 asks for.

⛔⛔ **But the recipe «ask by name and verify that it obeyed» does NOT close inside VA-API on
this driver**: `[M]` `vaQueryConfigAttributes` on the created config returns **the capability
mask** — 5270 on H.264, 5278 on HEVC — **identical whatever was asked**. ⇒ *Which*
mode is in force **cannot be read**. ⭐ Half the recipe works (the refusal); the other half must be
carried **downstream, onto the stream**: two known requests must give two different and predictable answers —
`[M]` CBR 5M → **5.01** · CBR 20M → **20.25** Mbit/s.

⛔ And `vaQueryProcessingRate` **answers** (640 000 macroblocks/s = 163.8 Mpixel/s) ⚠ **but it is identical
for H.264 and HEVC and for every level** ⇒ it is **a fixed table, not a measurement of this chip**, and it is
**eleven times** lower than what was measured. **Whoever sized a budget on it would be wrong by an order
of magnitude.**

#### The engines, read from the kernel

`[M]` `/sys/class/drm/card0/engine/`: `rcs0 · bcs0 · **vcs0 · vcs1** · vecs0`. **Two VDBOXes**, both
`hevc sfc`. GuC **disabled**, 32 EUs, ADL-S D0.
⚠ The kernel **does not declare** which VDBOX encodes ⇒ measured: ⭐ **both encode**, the driver
balances them by itself, and **which one takes a single stream changes from round to round**. ⇒ **The GPU does not
serialise: it parallelises over two, and stops at two.**

#### ⭐⭐ The ceiling is reached at **TWO** streams and does not move any more up to 32

| streams | 1 | 2 | 4 | 8 | 10 | 16 | **32** |
|---|---|---|---|---|---|---|---|
| total fps | 453 | **875** | 876 | 852-888 | 854 | 856 | **852** |
| per stream | 453 | 437 | 219 | ~108 | 85 | 53 | 27 |
| VDBOXes busy | 1 | **2** | 2 | 2 | 2 | 2 | 2 |

⭐ The split is **fair** (deviation between streams < 5 %) and **the cost of adding streams is zero**.
`[M]` **Opening** contexts: **2048** on a single `VADisplay` without a no from the driver; with one `VADisplay`
per context it stops at **1021**, ⛔ **and the error is `ulimit -n`, not the driver**.

#### What changes under load: **nothing**

`[M]` 1 / 4 / 8 encodings with the same request, 3000 frames each:
⭐⭐ **the stream is identical BYTE FOR BYTE** — `md5 d54653c7…` in CQP and `5e2acac6…` in CBR, **13 streams
out of 13** — and the CBR bitrate asked at 10M gives **10.003 Mbit/s everywhere, deviation 0.0 %**.
⛔ **No software fallback, ever.** ⇒ **Under load nobody decides in our place.**

#### ⭐ The hardware **is not a 35 W**, and it is thanks to the BIOS

`[M]` RPn 300 · RP1 650 · RP0 1550 MHz; under load it **nails itself at 1350** and stays there.
**Long round, 12 real minutes × 8 encodings** (78 768 frames per stream): **868.1 fps**,
frequency 1344.5 → **1350.0 MHz** (⭐ **it rises**), **25.2 W**, 59 → 64 °C, engines at **199.8 %**.
⚠ Two durations (§1.32): 200 s → 871.9 · 730 s → 868.1 ⇒ **the short round does not underestimate: here there is no
degradation to expose.**
⭐ `[M]` `intel-rapl:0` carries **PL1 = PL2 = 60 W**, not 35 ⇒ the premise *«un 35 W sotto otto
codifiche cala di frequenza»* **does not hold on this hardware** — and not thanks to us.

#### ⭐⭐⭐ And colour conversion runs on the **EUs**, not on the engine it was believed to

`[M]` bare encoder, 1080p CQP26, without conversion: **1 stream 449 fps · 8 streams 852** (1766
Mpixel/s) · **24.6 W** · 10 streams 854 · 24.6 W.
With the **BGRA → NV12** conversion in the path (`ffmpeg` with `hwupload` from memory) the work had
ended up on **`rcs0`, the render engine (the EUs)**, not on the `vecs0` believed to be dedicated, with a
drop in rate and more power. *(The numbers of the conversion from memory — rate, watts, seconds of
`rcs0` — no longer hold after phase 18: that route now converts on the CPU, not with the VPP; they
were removed.)*

⭐⭐⭐ **And it was the piece that explained §6.5**: there the bottleneck was `rcs0` at 99.5 %. ⚠ **And it also explained the
discrepancy with §6.4-bis**, which saw the VEBOX at 10.55 %: there behind it was **a real compositor**,
here only `ffmpeg`. ⇒ **Two different scenes, both true** (`LEZIONI.md` §1.28), and the conclusion
that survives all three is the same: ⛔ **the bottleneck is BEFORE the encoder.**

⭐ Two more: the HEVC against H.264 comparison of this bench went through `hwupload` from memory
*(measurement removed after phase 18; the valid one is §6.10)* · `async_depth` 1 / 2 / 4 **no
difference** ⇒ the product's value 1 **costs nothing**.

#### The budget of the bare encoder, and the table of §5.5 redone

`[M]` **≈ 1.8 Gpixel/s** in H.264 (900 per VDBOX, ⭐ **remarkably constant as the
resolution varies**: 900 at 480p, 940 at 1080p, 917 at 4K). *(The «con la conversione» value from memory is removed after
phase 18.)*

| §5.5 says | asks, for ten | is | ⇒ |
|---|---|---|---|
| 480p·25 «una cinquantina» | 102 Mpixel/s | **6 %** | ⭐ it rises |
| 1080p·30 «8-10, giusto al limite» | 622 Mpixel/s | **35 %** bare | ⭐⭐ **~29** |
| 4K·60 «una sola» | 4 977 Mpixel/s | 274 % | ⭐ **3.6** |

⛔ **And the shape of the limit is not the one §5.5 imagined**: it is not *«dieci sessioni sono il bordo»*
— it is **two VDBOXes of 900 Mpixel/s each, shared fairly, and the number of sessions does not count**
(thirty-two cost as much as two). ⭐ **The budget to keep is pixels per second, as §4.6 had decided**;
the value to put in it is 1.8 Gpixel/s **minus what is spent on conversion**.

#### The injected faults — **6 out of 6** and **7 out of 7**

Permissive driver (⇒ *«13 modi NON offerti accettati in silenzio»*) · re-reading impossible ⇒
**`None`, not `False`** · cap injected on the contexts · resolution 32768² ⇒ 0 contexts **with the
exact error** · calibration with **positive and negative** control · engines at zero (software fallback
simulated) · engines not measured ⇒ `None` · stream altered under load · bitrate at half · frequency
halved + thermal brake · meter calibration (6000/3000 ⇒ ratio **2.00**) · stress
arrived (3000 out of 3000).

⭐⭐ **And a fault that could NOT be injected was declared instead of being counted green**:
in the first round G5 was `None → None → None` because the healthy round lasted 0.4 s and the sampler did not
manage to take four samples. ⛔ **A fault not injected does not count**, and the bench
said so instead of giving a green.

#### The `[?]` of the hardware

⛔ **QVBR**, which is the mode the product really uses: CQP and CBR were measured, that is the two extremes in which
the predicate can be verified without ambiguity · **2560×1080**, the product's canvas: the three
rows of §5.5 were kept so as to compare them · capture, network, muxing, imported dmabuf: ⭐ **the number belongs to the
BARE encoder** · the **content**: synthetic scene only — `[?]` whether the deviation in **encoding
cost** between a real scene and grain is as big as the one in **bandwidth** · ⚠ the cost of the
conversion **without `hwupload`**: the measurement with the BGRA upload of 8 MB/frame is removed after
phase 18, and **the product imports a dmabuf at zero copy** · **sustained** 4K60.

### 6.7 ⭐⭐⭐ THE LOG WITH SEVERAL SESSIONS — **4.2 %**, and the blind test that is worth more than the percentage

`banchi/10-b96-registro.py` (+ `10-b96-terreno.sh`), `[M]` 24 Aug 2026 — **second round**.
Scene: **four real GNOME sessions of four different users**, scenes **different** from each other, 1080p
H.264, `--parlantina` on, phase 9 cures all on, under the lock.

#### The fraction — and the two that count are not the same

`[M]` window of **90.3 s at steady state**, **57 121 lines**:

| | |
|---|---|
| lines attributable **overall** | **25.3 %** (14 466 / 57 121) |
| ⛔⛔ **diagnostic** lines | **4.2 %** (647 / 15 328) |

By family: `fotogramma-spedito` 13 807 lines → **0.0 %** · `ciclo-cattura` 359 → **0.0 %** ·
`audio-blocchi` 359 → **0.0 %** · `silenzio-audio`, `cattura-danno`, `banda-video` → **0.0 %**.
⭐ Only `ritmo` and `rete-quic` attributable, at 100 %.
Reconfirmed over **111 900 lines**: 25.4 % / **5.0 %**, and ⭐ **zero ambiguous lines** — no line
carries discordant identifiers.
⚠ Without `--parlantina` the total share would rise to ~49 %, ⛔ **but the diagnostic one stays 4.2 %**:
*the lines that are needed are not detail lines.*
`[M]` **At eleven sessions** (log of §6.5, not its own): 29.7 % overall, **31.4 %** diagnostic,
`fotogramma-spedito` **0.0 %**.

⇒ ⭐ **Q10 is confirmed with a number**, and the number to quote is **4.2 %**, not the 63-100 % of the
static census: they are two different quantities — that one counted **the calls in the source**, this one
counts **the lines that really come out**, weighted by how much each repeats.

#### ⛔⛔ The blind test — and it is worth more than any percentage

Four tests, one per session: **a scene is switched off** and the log is asked **who stopped**.

| | |
|---|---|
| one *sees* that a series stopped | `[M]` **2 times out of 4** |
| ⛔ **the log says a NAME** | `[M]` **0 times out of 4** |
| whoever guesses the name gets it right | `[M]` **0 times out of 4** |
| ⛔ and in **2 tests out of 4** the separation by continuity of the counters **invented a fifth series** | with four live sessions |

⭐ **And the two errors of the meter are measured separately, as §1.33 requires.** On the lines that *have*
an identifier, it is hidden from them and one looks at whether the neighbour finds it again: `[M]` **3.6 %
right, 96.4 % WRONG, 0 abstained**. The **cautious** classifier, on the same lines,
abstains: **0 % wrong**. ⇒ ⛔ **Whoever guesses is wrong 96 times out of 100, and sends people to look at
someone else's desktop.**

#### ⭐ The interleaved lines: **the cure of 21 Aug holds**, and this is the data that proves it

`[M]` The new log: **201 898 lines, 0 orphaned, 0 interleaved, 0 truncated**.
⛔ **And the premise was false**: the longest line is **1 448 bytes**, that is **35 %** of `PIPE_BUF` —
*«le righe lunghe ci arrivano vicino»* **does not hold when measured**, and the truncation branch of
`registro.c` **has never fired**.

⭐ But «zero» counts only if the detector sees. **Eight logs sifted in full:**

| log | when | lines | orphaned | interleaved |
|---|---|---|---|---|
| `04-vero` | 20 Aug — ⛔ **before** the cure | 744 333 | **80** | **60** |
| `03-b17` / `04-b30` | 13-14 Aug | 557 873 | 5 | 4 |
| five logs | 22-24 Aug — ⭐ **after** | 1 513 463 | **0** | **0** |

A real one, from before the cure: `08:46:24.905 figlio 08:46:24.905 input ⭐ PRIMO fotogramma…
CHIAVEdispositivo «remotix virtual pointer» pronto` — ⛔ **plausible and false**.
⇒ ⭐ **The cure of 21 Aug (one single `write` per line) HOLDS**, and it is the first time someone
proves it instead of declaring it.

#### ⭐ What would be enough — **verified, not repeated**

`gancio_registra` receives `ctx` (= the `wt*`) and does `(void)ctx` (`webtransport.c:2116-2118`); the `wt`
carries `provenienza[80]` and `struct rcp_sessione *rcp`; `rcp_utente()` **already exists**.
⭐⭐ **163 lines out of 163 of `rcp.c` go through `reg(rcp_sessione *s, …)`**: the identity **is always there** and
is thrown away **in one place only**.

⇒ The **pid** in the format of `registro.c` cures **the 359 lines of the children in one line of code**;
`gancio_registra` cures **the 163 of `rcp.c` in one line**; there remain the 100 of `webtransport.c`, of which
**76** in functions that already have `wt *` and **24** in the hooks where `ctx` **is** the `wt*`.

`[M]` **The cost**: 632.8 lines/s with four sessions, 111.5 bytes/line, 70.6 kB/s ⇒ pid **+6.3 %**,
`[utente]` **+10.5 %**, both **+16.8 %**. ⭐ **And the test that closes it**: on the same log with the
remedy on **the blind diagnosis returns the right name**, at **+7.8 %** bytes.

#### ⭐ The six things nobody expected

1. ⛔⛔ **A `SIGSTOP` of 5 s to the children kills all four sessions**: `linea-morta causa=stallo
   stallo_ms=5000 usciti_byte=0 coda_video=8862 persi=0`. ⇒ **A stopped child leaves bytes stopped in the
   PARENT's queue**, and that is the stall the cure counts. ⭐ It is the **third** route by which the dead
   line detaches someone without the network being involved (the other two in §6.3 and §4.2).
2. ⭐ **`REG_CODIFICA` is the string `"video"`, identical to `REG_VIDEO`**: the 70 lines of
   `codificatore.c` cannot be told apart **even by area** from those of `webtransport.c`.
3. ⛔ **With all the children stopped the `figlio` area appears all the same**: the parent writes it too ⇒
   **not even the area separates parent and children**.
4. ⭐ **The log is not ours alone**: lines without a mark from **third parties** — `libopus`, SVT-AV1, the
   dynamic loader — without time, without area, without identity.
5. ⛔⛔ **To attribute a line one must sift the WHOLE log**: the bridge lines are
   **44 out of 201 898**. ⇒ If the log has been **rotated**, the steady-state line stays mute **for
   ever** — and the first round of this bench paid for it: reading the bridge only in the first 4 MB,
   `ritmo` turned out attributable at **28.6 %** instead of 100 %.
6. ⭐ **The most voluminous line of the product** is `rcp fotogramma N SPEDITO` — ~38/s per session,
   **always**, even without parlantina — and it is **0 % attributable**, although it is born where the session is.

#### The injected faults — **26 out of 26 bit**

Classifier that guesses (⭐ **measured, not hidden**: 44.4 % and 11.8 % wrong) · mute session
counted as «all attributed» (⛔ the naive count would say **100 % against 75 %**) · log read
before it was written ⇒ `None`, not «0 %» · ⭐ **interleaved lines injected on purpose** (found: 2
orphaned + 2 interleaved + 1 truncated) **and blind detector** unmasked · sample taken at startup
(⛔ the share would be **false for the better**: 50.8 % against 48.2 %) · calibration without a sample ⇒ `None` ·
nobody's lines christened «by proximity», 5 out of 5 · **dirty sample**.

#### The `[?]`

the corrected rule of the calibration sample was not re-run live (the lock had passed on) ·
⛔ **interleaving outside ext4** (NFS, pipes, `tee`): there the conclusion **would fall** · the cost of the
cure **on the product**: `src/` was not touched, the cost is arithmetic on the real lines.

### 6.8 ⭐⭐⭐⭐ THE REAL BROWSER — **two `[?]` closed, two findings WITHDRAWN, and a new defect that has nothing to do with multi-tenant**

`banchi/10-b2-browser.py` (+ `10-b2-filo.py`, `10-b2-terreno.sh`, `10-b2-lancia.sh`), `[M]` 24 Aug
2026, under the lock. **Real Firefox 140.14.0 ESR**, headless, driven by Marionette, arriving over
**Wi-Fi**. ⚠ `[?]` **One engine only**: Chrome was not tested.

#### ⭐⭐⭐ 1 · The two phase 9 cures do **NOT fight each other on a real browser**

| scene — **still** desktop, cures at defaults | outcome |
|---|---|
| **120 s** | ⭐ **SURVIVED** — still screen verified: **7 frames in 121 s** |
| **300 s** (the second duration of §1.32) | ⭐ **SURVIVED** — 10 in 302 s |
| control arm `--niente-audio-silenzio`, ⭐ **read from the server's `argv`**, not declared in words | ⭐ **SURVIVED** |

⇒ ⛔ **`linea-morta causa=silenzio` never triggered, in none of the three arms.** The defect of
§6.3 **stays true with the test client and does not bite the user.**

⭐⭐ **And the mechanism is measured, and it is not the one that had been hypothesised.** It is not Firefox keeping itself
alive: `[M]` on the wire, in the still window, **29 packets out of 29 from the client are ANSWERS** within
1 s — **zero spontaneous** (66 out of 66 in the long window), with median gap **5.003 s** and answer in
**2.9-3.3 ms**.
⇒ What keeps the line alive is **the `PING`s of OUR transport** (`tienila_viva_ns()` = half the
silence threshold = 5 s). ⛔ **The cure holds because the server asks, not because the browser talks**:
if one day the `PING` interval rose above the silence threshold, **the defect would come back
on browsers too**.

⚠ **And a number in the code is wrong by fifteen to nineteen times**: `webtransport.c` declares `[?]`
*«un tetto di ~26 byte/s per sessione»* with still traffic; `[M]` on the wire they are **497** and **399
bytes/s**. The server's packet is not short: it is a **full 1472 B** datagram, and the
browser's answer 69 B.

#### ⭐⭐⭐ 2 · The capsule of `RCP.md` §3.1 **ARRIVES, 10 times out of 10**

Full table (tree recompiled with `MAX_ATTACCATE=1`, the repository's `src/` **not touched**),
rejected one = real Firefox as a **different user**.

| | |
|---|---|
| capsule arrived at the browser | ⭐ **10 out of 10** — read **where it ARRIVES** (`wt.closed` resolving), not in the server log |
| code | **14 = `0x0E`** in all ten · ⛔ **never `0`**, which §3.1 forbids |
| how long after the `CONGEDO` | median **0.593 s** — the 500 ms of `WT_ATTESA_CHIUSURA_NS` plus the flight |
| what the user sees | *«quella sessione non si può servire»*, identical ten times |
| the server log, for comparison | armed 10, ⭐ **sent 10** |

⛔ **Meter calibrated first**: server killed with `SIGKILL` (no capsule possible) ⇒ the instrument
said **«error»**, not «capsule». Without that calibration, *«arrived 10 out of 10»* would have been a
platform promise, not a measurement.

#### ⛔⛔⛔ 3 · And the new defect, which **has nothing to do with multi-tenant and concerns everyone**

`[M]` A/B with the stage **cleared between one round and the next**, so that each one makes it **be born**:

| view width | DMA-BUF stride | child dead of **SIGSEGV** |
|---|---|---|
| **1268** — ⭐ *the one Firefox opens on its own* | 5072, ⛔ **not** a multiple of 64 | ⛔ **3 out of 3** |
| **1280** | 5120, a multiple of 64 | ⭐ **0 out of 3** |

The last line the child writes is its own — *«⛔⛔ il passo del DMA-BUF è 5072 … NON è multiplo di
64 … ⇒ Rimonto il palco sulla MEMORIA per questa tela»* — and **2 ms later it is dead**. The server says farewell
with `0x10` at **~4.6 s from the click**, **before the first frame**.

⇒ ⛔⛔ **A real user, with a window of arbitrary width, loses the desktop.** It applies only at the
**birth** of the stage (a re-attach does not go through there) — ⭐ and that is why the tuning rounds,
which re-attached, survived, and the campaign with the clearing **always died**.

⭐⭐ **And it is the same code §6.2 had already touched from the other end**: there the minimum canvas of
`SPECIFICHE.md` §5.5 (854×480 → stride 3416) was **refused** by the zero-copy guard. Here
one discovers that **the fallback to memory, which that guard invokes, kills the child.**
⚠ `[?]` Which line of `figlio.c` falls was not looked for: outside the mandate, delivered measured.

#### The injected faults — **59 out of 59**, and two real reds in the field

browser never connected ⇒ **«non-misurato»**, never «sopravvissuta» (and also: browser **hung** with the
duration expired) · screen not still (30 fps and 1 fps) ⇒ red · session ended by **ban / wrong
password / server off** counted as dead line ⇒ **«non-misurato»**: ⭐ *the reason is read* ·
⛔ capsule **declared arrived by reading the SERVER log** while the browser saw an
error ⇒ the two verdicts contradict each other, **and that is why it is read in the browser** · code `0` ⇒
the bench quotes §3.1 · `None` is not zero in six places · **17 out of 17** on the packet reader.
⭐ The two real reds: the server started with the **wrong** arm ⇒ *NON MISURO*; and the wire meter
calibrated with **25 known datagrams → 25 seen, 3200 bytes out of 3200** (deviation **0.0000 %**).

#### ⛔ The five **bench** defects paid for along the way

1. the witness on the wire wrote **in blocks**: stopped with a signal, the file had only the start
   line ⇒ *«il filo non ha visto passare NIENTE»* on a line that had carried the session for
   two minutes;
2. the `MutationObserver` **lost two lines**: two rewrites in the same event round arrive
   as **one** mutation. ⭐ The rule that comes out: **presence is read from the raw text, the time
   from the observer**;
3. the pattern `"BANNATO"` caught the **`"NON-BANNATO"`** of the server greeting ⇒ three healthy
   sessions declared «not measured». ⚠ **A false red, not a false green — and it costs the
   measurement all the same**;
4. ⛔⛔ **signal 15 was the bench itself**: `sgombra_palco()` sends `SIGTERM`, and the bench
   counted it as a product defect — *«figlio MORTO 5 su 5»* on **both arms**, that is an
   A/B in which the killer was the one measuring;
5. the width that counts is **`clientWidth`, not `innerWidth`**: between the two there are the 12 px of the
   scroll bar, ⭐ **and it is precisely that difference that led to discovering the SIGSEGV.**

#### The `[?]`

⛔ **Chrome was not tested**: `DECISIONI.md` §7.20 declares two of them, **one** was run · the
server's 1472 B packet every 5 s — padded `PING` or PMTU probe — **was not opened** ·
**which line falls** in the SIGSEGV · the path is **Wi-Fi**: *«clean line»* here means *«no
`netem` put in by me»*.

### 6.9 ⭐⭐⭐⭐ THE PREDICTOR — **yes, the budget can be computed in advance**, and the currency is the pixel

`banchi/10-b99-predittore.py` (+ `10-b99-lancia.sh`, `10-b99-misure.jsonl` with **41 points**,
`10-b99-sigilli.jsonl`), `[M]` 24 Aug 2026.

⭐ **The answer is the first of the three, with a condition**: it can be predicted — ⛔ **provided that the
machine's capacity has been measured once AT SATURATION**. And it is not an opinion: calibrated on the
first *k* steps, **before the machine has given way at least once**, the predictor answers
**«I don't know»** to every question above what it has seen, never a number. `[M]` Zero errors at every *k*, of
both kinds.

#### ⭐⭐ 1 · The currency is the **pixel**, and it is proved

`[M]` On the give-way points of the bare encoder:

| | 1920×1080 | 3840×2160 | deviation |
|---|---|---|---|
| **Mpixel/s** at the give-way | 1856.0 | 1866.9 | ⭐ **0.6 %** |
| fps at the same point | 895.1 | 225.1 | ⛔ **74.9 %** |

⇒ **The quantity that stays constant as the canvas varies is the pixel per second**, and the fixed term per
frame is worth **0.0162 Mpixel** — a square of 127×127, negligible.

⛔⛔ **And a new trap, of the §CLOCK family**: `us_codifica` per frame is a
**LATENCY, not a COST**. Its curve has a fixed term of **0.400 Mpixel**, **twenty-five times**
the real one ⇒ whoever calibrated the budget on it **would overvalue a 480p canvas by 2.0 times**.
⚠ **And it is the number §3.2 proposed as «il costo vero»**: wrong **twice** — wrong engine
*and* wrong quantity.

#### 2 · The function, and ⛔ **before the pixels one looks at the LATENCY**

```
regge(dentro, nuovo)  ⟺  domanda(dentro) + tela(nuovo) × ritmo_max  ≤  C
```

`[M]` **C = 479.8 Mpixel/s** (i5-13500T · UHD 730 · real GNOME desktops · 1080p · H.264 · cures on)
— the **maximum work delivered**, at the sixth step. Beyond that point the total does not rise: **it falls**.

⛔⛔ **And the count on pixels lies exactly when it is needed**: `[M]` at eight sessions the total delivered is
**26.6 Mpixel/s against 480** ⇒ it would say *«c'è posto per altre cinque»* **while everyone sits at 1.5
fps**. ⭐ The column that saves is the **latency**, and the threshold **is measured, not chosen**: `[M]`
healthy ≤ **13.1 ms**, broken ≥ **39.9 ms**, ⭐ **no overlap** ⇒ **22.9 ms**.

| rule | false NOs | false YESes | cap **saturated** | cap **still** |
|---|---|---|---|---|
| delivered | 0 | 0 | 6 | ⛔ unlimited |
| ⭐ **reserve 50 %** | **0** | **0** | **6** | ⭐ **10** |
| worst | 1 | 0 | 5 | 6 |

⭐⭐ **The proposed rule is «reserve 50 %», and the cap that comes out of it for still sessions is TEN** — that is
exactly the number `SPECIFICHE.md` §5.5 promised, found again **by measurement instead of by
promise**. And the knob stays in the director's hand: `F=0` is «delivered», `F=1` is «worst».

**The margin, on both sides** (`LEZIONI.md` §1.33): `[M]` **+1.65 %** above the highest demand that
held, **−13.7 %** below the lowest that gave way ⇒ ⭐ **the margin on the side that starves everyone is
eight times the one on the side that costs one user**, which is the right direction.

#### ⛔⛔ 3 · The WAKE-UP is the real flaw, and phase 9 cannot cure it

`[M]` A **still** session delivers **0.05** Mpixel/s, a **saturated** one **82.0**: a factor of
**1 640**. ⇒ A budget counted on what is delivered can be **overshot 1 640 times by a wake-up**,
⛔ and **the phase 9 regulator cannot remedy it**: it lives in the parent and stops frames **already
encoded** (§3.2). ⭐ The 50 % reserve limits the overshoot to **2×**.

#### ⭐⭐ 4 · The mechanism of the cliff — the buffer lead is **verified and CORRECTED**

Verified on the code: `cattura.c` · `parametri_di_consumo()` asks for `RANGE(6, 4, 8)` · `cattura.c` · `parametri_di_consumo()` *«al massimo DUE»* ·
`cattura.h` · `REMOTIX_CATTURA_H` `buffer_distinti` **is already counted** · `codificatore.c` · `converti_sulla_gpu()` `vaSyncSurface`, which the
comment next to it calls *«il rilascio»*.

⛔ **And the prediction deduced from the timings is REFUTED**: it had been deduced that `buffer_distinti ∈ {3,4}`; `[M]`
read in the log of the climb to eleven: **6 in 524 lines, 8 in 65**. ⚠ *(Not a blind comparison: that
log is older than the seal — it counts as a **check**, not as a forward verification.)*

⭐ **With the real value the account improves**: lead = (6 − 2) × 16.67 = **66.7 ms** · `[M]` last step
**below** the lead is the **7** (39.9 ms) · first **above** is the **8** (654.3 ms) ⇒ ⭐⭐ **the lead is
crossed exactly at the cliff.**

⛔⛔ **But it does NOT explain the first worsening** (step 7, which sits **below** the lead): that is
**contention**, and the count on pixels explains it. ⇒ ⭐⭐ **They are TWO mechanisms on TWO different steps**, and
confusing them would make one blamed for the damage of the other.
⚠ And the constraint is **loose**: the data admit any lead between 4.4 and 41.3 buffers ⇒ **compatible
with the arithmetic, not a confirmation of it**.
⛔⛔ **And `buffer_distinti` is not the same for everyone**: 6 for 89 %, 8 for 11 % ⇒ **two sessions
of the same round have leads differing by 50 %, and the product does not know it.**

> ##### ⛔ And the buffer release is **AFTER THE WHOLE encoding**, not after the conversion — *correction*
>
> The first account said, on the faith of the comment of `codificatore.c` · `converti_sulla_gpu()`, that Mutter's buffer
> comes back as soon as the conversion has finished. ⛔ **The code says something else**: the release is at
> **`figlio.c`**, **after `codifica_e_manda()` in full** — and the comment next to it wants it there
> on purpose: *«si chiama DOPO la codifica… spostarla di due righe più in su rimetterebbe in piedi le due
> schermate che si alternano»*.
>
> ⇒ ⭐ **The window in which the compositor's buffer is OURS is not the conversion alone: it is
> conversion + encoding + SENDING** — and the sending is a **blocking** `send()`
> (`figlio.c` · `figli_spegni()`). ⇒ The threshold is **easier to break through** than it had been told, and — what
> matters more — it is made of **the three TRATTO entries the bench already reads**: ⭐ **the two sides
> of the inequality are measured in the same round.**
>
> ⭐⭐ **And the two «two»s are read from the structure, not from the comments**: `cattura->posto` is **one single
> box** and whoever arrives returns at once what it finds (`cattura.c:1160-1165`); `cattura_prendi()` takes
> away the frame (`:2054`) and whoever consumes returns it in `cattura_fermo_libera()` (`:2197`) ⇒ **one
> in the box, one in the hand of the reader**. And the 6 of `cattura.c` · `parametri_di_consumo()` are a **requested minimum**, not
> an order: how many the producer gives is said by `buffer_distinti`, which is **counted**.
>
> ⇒ ⭐⭐⭐ **threshold = (buffers − 2) × period**, and the calibration shows the thing that counts: `[M]` with 6
> buffers **66.67 ms**, ⭐ **with only 4 buffers 33.33 ms** — that is **the cliff moves with the number of
> BUFFERS, not with the number of sessions**. It is precisely the quantity the product can compute:
> buffers negotiated, buffers held, cadence requested.

#### 5 · The practical piece — ⭐ **no new channel is needed, except one**

Eight predicates verified on the real `src/`, **not repeated from §3.2**:

- ⭐ `main.c:394 deposita_fotogramma()` receives **every** frame with width, height, instant and
  bytes; `figlio.c` calls it **without guards** on «someone is watching» ⇒ **the parent sees the
  ghosts too** of §3.2;
- ⭐ the newcomer's ceiling is already there **at `CIAO`** (`video.misura_massima` → `rcp.c` · `MAX_ACCUMULO`), ⛔ **but it is not
  exposed by `rcp.h`**;
- `main.c` · `aiuto()` the verdict has transport and children in hand, and from there one goes back up to the newcomer's RCP
  session ⇒ ⭐ **the no can be said where it must be said**;
- ⛔ no pixels/s counter exists in `src/`; `us_codifica` does not leave the child — ⭐ **and it is not
  needed**.

⇒ ⭐ **The minimum**: an **accumulator** in `deposita_fotogramma()` and an **accessor** in `rcp.h`.
⛔⛔ **The only new number is `buffer_distinti`**, which lives in `cattura.c`, that is **in the child**: without
it the lead cannot be computed.

#### ⛔ 6 · And the fact that scales everything down: **compositing is not observable by the product**

`[M]` The compositors draw **60.0 fps** with one session and **41.96** with eleven: they lose
**30 %** while our chain loses **98 %**. ⇒ At step 11 **~958
Mpixel/s** are still being composited and **21.6** are delivered.
⭐⭐ **The «capacity» of 480 Mpixel/s is what is LEFT OVER after the compositors — and their slice grows with the
number.** ⇒ The product's budget governs **its own half**, not the machine.

#### The injected faults — **86 cases, 0 reds**

Meter halved · data from **another chain**, from **other hardware**, from the **bare** encoder ⇒
**«I don't know»** · session without a canvas ⇒ «I don't know», never zero · forty still ones plus one ⇒ the three rules
give three different answers · lead with 6/4/3/8 buffers, `buffer_distinti` not read ⇒ `None`, all
held ⇒ **zero and not «I don't know»** · ⭐ **measurement older than the anchor, anchor removed, predictions
retouched after the seal, non-existent seal** ⇒ **no comparison** · fake machine with the cap at 11
⇒ 6 false NOs, with the cap at 3 ⇒ false YESes · ⛔ **bare encoder capacity transferred onto the real
desktops** ⇒ it would admit **~22** sessions where 6 fit · climb that never makes it give way ⇒ ceiling
**not seen** · latency gate removed ⇒ false YES on eight throttled · ⭐ a machine that spends
**frames** ⇒ the currency test answers «frame» (**the negative control**) · and on the
sources: counter already present ⇒ red, `us_codifica` out of the child ⇒ red.

⭐⭐ **And three defects were found by the certification in the predictor itself**: (a) the count on pixels
gave **false YESes after the cliff** — cured with the latency gate; (b) the threshold refused by
**rounding** a state that had held; (c) ⛔ **the lead check was a TAUTOLOGY**
(it compared the lead step with «the last below plus one») — rewritten against the cliff, which is
an independent fact, **and now it can say no**.

#### The `[?]`

⛔ **The blind forward verification has not happened yet**: `[M]` in three hours the lock passed
through seven turns and **its pilot never won the race**. The four predictions stay
**sealed** with the fingerprint, and whoever wins a turn can have them judged blind ·
⛔ **the capacity is verified on ONE canvas only** (1920×1080): outside it the predictor **declares that it
extrapolates** · ⚠ the threshold of 22.9 ms is **of this scene**, and the parent's latency is an
**upper bound** of the holding time ⇒ cautious in the right direction, but it is not the quantity of the
mechanism.

⇒ ⭐⭐⭐ **The shape of the product that comes out of it**: `--budget-mpixel-s N` **with a function behind it**
(rule «reserve», with the knob `--riserva`), the no said in `consegna_verdetto()` **before**
`figli_assicura()`, and `--tetto-sessioni` remaining **only an administrative cap, not a limit**.
⛔ And one thing the product **cannot** do: `--budget-mpixel-s` **does not self-calibrate** — before
the machine has given way once, the capacity is **a lower bound, not a ceiling**.

### 6.10 ⭐⭐⭐⭐ HEVC AND QVBR — and ⛔ **the product prefers HEVC, not H.264**

`banchi/10-b88-saturatore.py` (extended) + `10-b94-ferro-carico.py` (extended), `[M]` 24 Aug 2026,
synthetic scene, zero copy from DMA-BUF, `EncSliceLP` **verified on the driver**, under the lock,
⭐ **strangers on the video engine `0,0 %` in every row**.

#### ⛔⛔ The fact that reorders the columns: **the product negotiates HEVC first**

`rcp.c:1829 NOSTRO_CODEC "hevc,h264"` · `RCP.md` §4.3 chooses **in the client's order** ·
`pagina.html:831 PREFERENZA = ["hevc","h264"]`.
⇒ ⭐ **On every browser that decodes HEVC the product sends HEVC**; **H.264 is the fallback**.
⚠ The saturator's header said *«il codec è H.264, quello che il prodotto negozia davvero»*:
it is **half true**, and it was corrected.
⭐ **And the negotiated depth is 8, that is HEVC Main — not Main10**: `[M]` the two cost the same (83.0
against 83.1 %), so the budget does not change, ⛔ **but what must be written in the documents changes**.

#### ⭐⭐ The ceiling in HEVC: **2.33 Gpixel/s against 1.86** — **+25 %**

| cell (15 s) | H.264 High | HEVC Main10 | HEVC Main |
|---|---|---|---|
| 4K60 N=2 | 995.5 Mpx/s · **52.1 %** | 995.6 · **41.5 %** | 995.5 · **41.4 %** |
| 4K60 N=4 | 1865.8 · 99.7 % ⛔ **gives way** | 1990.4 · **83.1 %** ✅ | 1990.3 · **83.0 %** ✅ |
| 4K60 N=6 | — | **2322.0** · 98.7 % ⛔ gives way | **2344.8** · 98.7 % ⛔ gives way |
| 1080p30 N=24 | 1494.7 · **79.7 %** | 1494.9 · **63.0 %** | — |
| 1080p30 N=32 | 1855.9 · 99.5 % ⛔ **gives way** | 1992.9 · **84.2 %** ✅ | — |

`[M]` **At every common cell HEVC costs ~21 % less engine time** for the same pixels — and the two accounts
agree with each other: −21 % of time ⟺ +25 % of ceiling. ⭐ **And twice the sustained 4K streams**:
four against two.
⛔ **Again a cliff, not a knee**: at 4K60 the median latency goes from **5.4 ms** (N=4) to
**1 716 ms** (N=6).

⛔ **And the two columns stay SEPARATE**: same scene, same QP, 1080p30 N=1 → H.264 **8.976**
against HEVC **9.804 Mbit/s** (**1.09×**). ⭐ **HEVC costs less GPU and more bits**, and the ratio **is not
a constant** — it is the wound phase 9 had already paid for.
⚠ **Discrepancy declared and not forced** (`LEZIONI.md` §1.28): §6.6 had a smaller comparison
on `ffmpeg` with `hwupload` **from memory** and in fps *(measurement removed after phase 18)*; here it is **21 %**,
on the product's encoder **with zero copy** and in engine time **at saturation**. **Two different
quantities, same direction.**

#### ⛔⛔ QVBR: it is there, it works — **and nobody switches it on**

`[M]` Read in `src/codificatore.c` · `modo_bitrate_voluto()`: two modes, asked **by name**, never `auto`. ⛔ **The
default is CQP**: `main.c:657 tetto_banda_mbit = 0` (invariant **I6**), and the cap **is not among the
five cures on** of `CODER.md` §2-bis.
⇒ ⛔ **Today the product does not use QVBR.** ⭐ The bandwidth cure of phase 9 **exists, works, and is not
switched on by anyone**.

`[M]` **QVBR obeys**, 1080p30, calibrated meter:

| scene | CQP 26 | QVBR floor 10 | floor 20 | floor 40 |
|---|---|---|---|---|
| **hard** (grain) | ⛔ **162.643** Mbit/s | **5.717** | **11.423** | **21.989** |
| **easy** (flat colour) | 0.017 | 0.020 | 0.020 | 0.020 |

⭐ **It aims at the OPERATING POINT, not at the wire**: 95 · 95 · 92 % of the point, and two known requests give
×2.00 and ×1.92 against a ×2.00 asked. ⛔ **It is not a CBR in disguise**: on the easy scene it spends **×1.18
of CQP**, not the 12 Mbit/s a CBR would have spent.
⭐ **And the QP under QVBR counts**: from 20 to 44 the stream goes from **15.010 to 1.713 Mbit/s** — **8.8×**.
⇒ **The phase 9 degradation ladder is not a no-op.**

**Under load**: ⭐⭐ **13 streams out of 13 identical** — fingerprint, bytes and frames — **even in QVBR**;
and on `ffmpeg` 12 out of 12. ⇒ **Not even in QVBR does anyone decide in our place.**
⭐ And a new number: at ×8, CQP **876.8** fps, QVBR **816.0**, CBR **812.8** ⇒ **a regulated mode
costs ~7 % of rate**.

#### The injected faults — **11/11 + 11/11 + 30/30 predicates**

HEVC round counted as H.264 ⇒ RED *«è il flusso a dire il codec»*, and the reverse · mode asked and
not obtained ⇒ RED *«CHIESTO QVBR (5), il contesto rilegge CQP (1)»* · target missed ⇒ RED
**with the number** · QVBR wire overshot · `avcodec_open2` failing.
⛔ **And the anchor**: codec, depth and mode are read **from the stream produced** (composed on the SPS) and
from the **re-read** context, ⭐ **never from the command given**.

#### ⛔ The three bench defects paid for, and the first is the one that counts

1. ⭐ **The first red belonged to the bench, not to the product**: on a flat colour the three QPs all gave
   `0,0200` because the stream was **at the bottom**. ⇒ The bench was about to **declare a product
   defect that was a choice of scene**; now it has the **third outcome** (`None`, with written **which**
   redo is needed) and redone on a middle scene it gives **8.8×**;
2. `rampa` called the ground check with `LUCCHETTO_MIO=1` **before** taking the lock
   ⇒ **guaranteed red on something true but wrong**;
3. ⚠ **On the lock, five seconds lose against one**: `prendi()` retries every **5 s** while
   other pilots retry every second ⇒ a 45-minute window lost. It is the **race** of §7.3, with
   one more asymmetry.

#### The `[?]`

⛔ **The ceiling at 1080p30 in HEVC was not reached**: N=32 holds at 84.2 % — what stopped was the
**bench's scale**, not the hardware · **QVBR on HEVC**: the driver declares it, the test on the stream was not
done · ⛔⛔ **QVBR with a REAL desktop behind**: the «easy scene» is a flat colour, **not
a desktop** — ⚠ *and it is precisely the scene on which phase 10 of v1 was reset* · the bitrate meter is
calibrated on `ffmpeg` in CBR, because **the product cannot do CBR** and cannot give itself a known target ·
synthetic scene ⇒ the Mbit/s **are not those of the product** · no long duration on this column.

⚠⚠ **And a declaration of honesty about the ground**: the **HEVC Main10 ramp ran with the ground RED**
(servers of other benches on, plus the order defect on the lock) — ⭐ the strangers on the video
engine were `0,0 %` in every row, **but the machine was not idle**. ⭐ **The QVBR study and the HEVC
Main ramp ran with the ground 21 out of 21 GREEN.**

### 6.11 ⭐⭐⭐⭐⭐ THE COMPOSITING CEILING — **0.97 Gpixel/s**, and the number the phase was looking for

`banchi/10-b95-composizione.py`, `[M]` 25 Aug 2026, i5-13500T · **integrated Intel UHD 730**,
ground `10-b0` **21 out of 21**, lock in hand, a scene that **damages the whole surface at every
frame**.

| N | `rcs0` | composited Mpixel/s | GT | RC6 |
|---|---|---|---|---|
| 1 | 14.59 % | 124.4 | 1267 | 66.5 % |
| 6 | 89.53 % | 746.3 | 1374 | 3.1 % |
| ⚠ 7 | **99.21 %** | 870.9 | 1454 | 0.0 % |
| ⭐ 8 | 99.71 % | **992.1** | **1542** | 0.0 % |
| 11 | 99.53 % | 957.7 | 1542 | 0.0 % |

⭐⭐ **And here the §CLOCK has no ambiguity**: at saturation the GT **nails itself at 1542-1550 MHz (RP0)** and
RC6 goes to **0.0 %** ⇒ the ceiling is read **at the clock's maximum**.

⛔⛔ **The bottleneck is this, not the encoder**: **0.97 against 1.86 Gpixel/s** — compositing gives way
first, by a factor of **1.9**.
⭐⭐⭐ **And the account matches what the user saw**: a 1080p desktop at 60 Hz is worth **124.4
Mpixel/s** ⇒ **7.8 fit**, and `rcs0` passes 99 % **at the seventh**. ⇒ **Six fit comfortably** — ⭐ **the
same answer as §6.5, for a completely different quantity and with a different bench.**

**The law** (ramp N=1..6): `rcs0 % = 0,12068 · cambio[Mpx/s] − 0,842`, rms **0.304 points**,
**R² 0.99986**, intercept **zero within the error**.
⭐ **And the line does not extrapolate, with the confirmation inside**: 100/0.12068 would give 835.6 Mpixel/s, the
hardware does **992** ⇒ 992/835.6 = **1.187** against 1542/1342 = **1.149**, which **agree within
3.3 %**. ⇒ It is the independent proof that `drm-engine-*` measures **time × frequency**.

#### ⭐⭐⭐ The breakdown — and **the product's colour conversion is NOT on the EUs**

| owner | engine | `[M]` |
|---|---|---|
| compositor + capture | `rcs0` | **14.54 %** (GT 1337) |
| compositor alone, nobody connected | `rcs0` | 28.37 % (⚠ GT 612) |
| ⭐ **colour conversion** | `rcs0` | ⭐ **0.00 %** |
| ⭐ **colour conversion** | `vecs0` | **14.53 %** (55.9 % at five) |
| encoding | `vcs` | 8.47 % out of **200** |

> ##### ✅⛔ AND THIS CORRECTS §6.6 — *two different scenes, and the product's is the other one*
>
> §6.6 had found the conversion **on `rcs0`**, not on `vecs0`, with a drop in rate and more watts
> *(numbers removed after phase 18)*. ⚠ **But that was `ffmpeg` with `hwupload`, 8 MB per
> frame.** ⭐ **The product imports a dmabuf at zero copy**: `[M]` **zero on the render
> engine, everything on the VEBOX** — which **is never the bottleneck**.
> ⇒ ⭐ The `[?]` the assignment marked with the star is **closed**, and in the good direction: **our
> conversion steals nothing from the compositor.** ⛔ **What saturates `rcs0` is the COMPOSITOR, and it alone is enough.**

#### ⭐⭐⭐ And the cost **is not proportional: there is a step**

`[M]` At ~1350 MHz, one desktop alone: **19.0 Mpixel/s → `rcs0` 8.13 %** · **124.4 Mpixel/s → 13.69 %**.
⇒ **6.5 times the change costs 1.68 times.**

```
rcs0 %  ≈  7,1 %  (fisso, per desktop che compone)  +  0,053 % per Mpixel/s
```

⇒ ⭐⭐ **Half the cost is a fixed toll for merely being a live desktop at 60 Hz.**
⇒ ⛔ **The budget can be computed in advance, but with TWO terms, not one** — and the fixed term is
the one that decides how many «quiet» sessions fit.
⚠ `[?]` **Only two points, taken in two different phases**: the mode that would close it (`ritmi`) exists and
is correct, ⛔ but its round **never won the race for the lock**.

#### ⛔⛔ And the dead-line defect, seen a **second time** — and **wider** than it was

`[M]` `causa=silenzio silenzio_ms=10044 persi=0`, on a **healthy** session that a moment earlier
was delivering **60 commits/s and 5 524 bytes per frame**.
⇒ ⛔⛔ **It is not the «still desktop» of §6.3: TEN SECONDS of gap between two scenes are enough.**
⭐ And the bench **does not switch off the cure to pass**: it removes the gap.

⚠ And a second side finding: **the child does not go away when the client disappears** — after 90 s
it is still there. ⭐ But on the GPU it is at **zero** (`rcs0` 0.00, `vcs` 0.00): **it holds the slot, it does not work**
— which is the good half of the ghost of §3.2.

#### The injected faults — **52 out of 52**, and ⭐ **eight negative controls**

The five requested, each one run: still screen declared as a changing scene (⭐ **by the rate AND
by the bytes**) · meter attributing another DRM client to `gnome-shell` · changing population ⇒ `None`
· GT moving between steps ⇒ **null comparison** · step read from the previous one.
⭐⭐ **And the red was really seen**: removing **one guard at a time** the certification drops
to 48/49/51/51/51/51/51/51 out of 52 — **eight guards, eight drops**.

⚠ **Three defects belonged to the bench, found while measuring**: (a) the GT mean counted the samples at
**0 MHz** ⇒ it answered *«how long it was awake»*, not *«at what frequency it worked»*; (b) the
refusal on **any** turnover of DRM clients — `[M]` 8 vanished in 3 s, none of them its own: refusing there
would mean **never measuring**; (c) red on every `gnome-shell` not its own ⇒ **red on correct
code**.
⭐ **And one was avoided by thinking about it beforehand**: at the ramp the commits collapse from saturation, and the
«still screen» predicate would have given **red to the result the ramp is looking for**.

#### The `[?]`

⛔ **Capture cannot be isolated**: Mutter delivers the frames **inside `gnome-shell`** ⇒ on the GPU it is the
**same DRM client**, and the difference between the two steps had the GT at **612 against 1337 MHz** —
⭐ **the bench refused to subtract** · ⛔ **«no encoding» steps do not exist in this
product**: no option switches on the session without the encoder, and the child builds capture,
conversion and encoding **in one single stretch** — declared, not estimated · ⛔ **the cost step rests
on two points** · ⚠ the case is the **hard** one ⇒ the number is **a floor**, not a prediction for
ten users reading their mail.

⭐ And a confirmation of the trap of §7.3, from yet another end: `pgrep -c -f "remotix.*--porta 8110"`
answered **3** on a machine where there was none of its processes — it matched **the command line
of the shell running it**. With the pattern `--porta 811[0]`: **none**.

### 6.12 ⭐⭐⭐⭐⭐ THE CLIMB ON THE **REAL DESKTOP** — **ELEVEN fit, and there is no cliff**

`banchi/10-b92-dieci.py` extended (3 011 → 4 608 lines) + `10-b92-scene.py`, `[M]` 24-25 Aug 2026,
eleven real users with real headless GNOME, steps of **45 s at steady state**, under the lock, cures
on.

#### ⭐⭐⭐ First the anchor: **the saturated scene finds the SIX again**

`[M]` Redone row by row: **6**, identical to §6.5, with the cliff **at the eighth** (27.63 → 1.62 fps).
⇒ ⭐ **The comparison among the three scenes has a meter**, and what follows counts.

#### And then the fact that reorders the phase

| | **still** (11) | ⭐ **real** (11) | **saturated** (6) | **saturated** (11) |
|---|---|---|---|---|
| fps each | 0.02 | **9.79** | 38.54 | ⛔ 0.97 |
| bytes/frame | 203-389 | **4 824** | 5 591 | 4 909 |
| **median latency** | 9-12 ms | ⭐ **8.0 ms** | 11.2 ms | ⛔ **1 134.7 ms** |
| GPU **render** | **0.0 %** | **22.3 %** | 88.8 % | 99.6 % |
| GPU **VEBOX** | 0.0 % | ⚠ **24.1 %** | 52.6 % | 0.9 % |
| GPU video | 0.0 % | 11.4 % | 26.9 % | 1.3 % |
| CPU (20 cores) | 4.8 % | 10.8 % | 19.1 % | 18.2 % |
| total PSS | **2 028 MiB** | 3 382 MiB | 1 257 MiB | 2 209 MiB |

- ⭐⭐ `[M]` **The first session goes from 10.61 to 9.79 fps from the first to the eleventh: −7.7 %**, under the
  tolerance. ⇒ ⛔ **ZERO violations of I1 on the real desktop**, against the **37** of the saturated scene.
- ⭐ **The latency does not move**: 8.4 → 8.0 ms. On the saturated one it goes from 9.9 to **1 134.7**.
- `[M]` **Zero keyframes** on all three arms, even inside the collapse — ⭐ it confirms `LEZIONI.md`
  §1.34: **the column that warns, here, is the latency**.
- ⭐ `[M]` **Eleven STILL desktops cost ZERO GPU**: 0.0 % on all four engines, RC6 **100 %**,
  GT **0 MHz**, 0.11 Mbit/s in all. ⇒ **There the constraint is memory** (2 028 MiB), not the card.
- ⭐ And the «vero» scene is **the same definition as §6.4-bis**: `[M]` **4 824-5 375 B/frame**
  against the **5 130** measured there. **The two measurements match**, and they come from two different benches.

> ### ⇒ ⭐⭐⭐⭐ **THE «SIX» WAS THE NUMBER OF A SCENE NO USER PRODUCES**
>
> ⛔ And the ceiling of the real desktop **was not found**: `[M]` it was **the users that ran out, not the
> machine** — eleven sessions sit at **22-24 %** of the GPU. ⚠ Extrapolation would say `[?]`
> ~46 sessions, **and that is four times outside what was measured: it is not reported as a number.**
>
> ⭐ The director's judgement (`fasi/10-multi-tenant-e-il-budget.md` §S.2) — *«sei su un'integrata modesta non è un cattivo
> risultato»* — comes out **strengthened**, not refuted: on the scene in which the user lives
> **at least eleven fit, without the first one noticing**.

#### ⭐⭐⭐ The law of the cost — **proportional, without steps**

Measured **twice by two independent routes**, with the input taken from the counter of the **scene's
draws**, not from the frames delivered:

| route | law | R² | max error |
|---|---|---|---|
| **saturated** climb, 6 points | render % = **−0.675 + 0.1196 ×** Mpx redrawn/s | **0.9999** | 0.7 % |
| **knob on one session**, 4 points | render % = **+0.024 + 0.1172 ×** | **1.0000** | 0.4 % |
| **real** climb, 11 points | render % = **+0.264 + 0.1494 ×** | **0.9999** | 1.1 % |

⇒ ⭐ **The budget can be computed**: no step, intercept ≈ 0, slopes within **2 %** of each
other. ⛔ And the cost grows **right into the cliff**: at the seventh saturated step the demand (871
Mpx/s) exceeds the ceiling (≈ 842 from the line), and from there **the product stops delivering**.

⭐ **And the cost is NOT proportional to the changed area**: the two slopes differ by **25 %** between
full screen and window. Solving on the two arms:

```
render %  =  0,145 × (disegni/s)  +  0,0494 × (Mpixel ridisegnati/s)
```

⇒ at 1080p **59 % of the cost of a redraw is FIXED**, independent of how many pixels changed.
⚠ **A two-point solution, not a line with an error**: a hypothesis consistent with both arms, **not a
validated law**. ⭐ **And it is the same end §6.11 took from the other side** — there `7,1 % fisso +
0,053 % per Mpixel/s`, here `0,145 per disegno + 0,0494 per Mpixel`: **two benches, two routes, the
same two-term shape.**

#### ⛔⭐ And the project's meter was wrong for this scene

`[M]` **The floor of 25 fps** (`SPECIFICHE.md` §2.1) **gave RED with ONE single session and the
GPU at 2.2 %**: a scene of **tears** does not produce 25 frames per second, and it must not.
⇒ ⛔ **All 66 reds of the «vero» arm were that; ZERO belonged to the product.**

⭐⭐ The meter was replaced with the **yield** — how many of the scene's draws **arrive**: `[M]`
**0.64-0.73 on an idle machine**, and on the saturated scene it collapses to **0.42-0.46 exactly at step
7**. ⇒ ⭐ **The new meter finds the six by itself, by a route different from I1.**

#### ⭐ The other four things nobody expected

1. ⭐⭐ **The engine that runs out first CHANGES with the scene**: on the saturated one it is `render`; on the
   real desktop, at eleven, **the VEBOX overtakes** (24.1 % against 22.3 %) — ⛔ **and the VEBOXes are
   ONE**, the VDBOXes two. ⇒ It confirms the prediction of §6.4-bis, which had been taken **from one alone**.
2. ⭐ **The memory of a real desktop costs 60 % more**: **307 MiB** PSS per session against 190
   for the saturated and 184 for the still — they are the open applications.
3. ⛔ **`--certifica` went knocking at the test machine** while declaring it did not — ⭐
   found **by looking at the clock** (0.23 s against many seconds), not the code.
4. ⛔ The case that shows why **the order of the columns matters**: the frozen scene made **1 368
   bytes/frame**, that is **above** the floor of 600 ⇒ **the bytes alone would have given it green**.
   It is **E15** reproduced, and the **draws** counter catches it.

#### The injected faults — **75 cases, 0 reds** (they were 42)

The 42 old ones run again **intact**, plus 33 new: frozen «real desktop» ⇒ red **on the draws**
· scene that draws 14/s and 1.5 arrive ⇒ red · draws not read ⇒ `None` · «still» that delivers
25 fps ⇒ a red that **names** screensaver, clock, notification · ⛔ **the anchor that finds 5 and
the one that finds 8** ⇒ the bench **refuses the comparison** · ⭐ the capacity dropping from 8 to 4 for an I1
red **the rate did not see** · step cost ⇒ the error denounces it · line on two points ⇒
`None` · shm reader **calibrated with known injected values**.

#### The `[?]`

⛔ **Where the ceiling of the real desktop is** — the users ran out · ⛔ **the cliff on the real
scene**: within eleven **it does not exist**, at what number it is nobody knows · ⛔ **the real network**: the clients
run on the same machine ⇒ the wire is **counted, not tested** · ⛔ **the image**: the bench does not
say *«si vede peggio»* — ⭐ **that is said by the director**.

### 6.13 ⭐⭐⭐ THE LOGIND GUARDIAN — **the defect is real, the multiplier is not**, and it bites long before detaching

`banchi/10-b97-guardiano.py` (+ `10-b97-terreno.sh`, `10-b97-innesta.py`), `[M]` 25 Aug 2026, with
the **fake guardian** injected only on the adapter that `main.c` · `ABBANDONO_PREDEFINITO_MS` declares it put there on purpose
for this. ⛔ The repository's `src/` **not touched**, the two `md5`s declared.

#### ⭐ The defect **reproduces**, with the signature deduced by reading

`[M]` `causa=stallo stallo_ms=6004 offerti=52 usciti_byte=0 persi=0 permille=0` — the stage was producing,
**nothing went out**, the line was **clean**, and the product told the user *«la linea è
MORTA»*.

#### ⛔ But **the multiplier is not the one the finding named**

`[M]` **`ListSessions` does NOT grow with the number of logind sessions**: from 63 to 72 sessions the medians
go **2.58 → 2.27 ms**, slope **−34.6 µs per session** — flat, within the noise. The worst
call seen anywhere is **13.14 ms**, against a stall threshold of **5 000**: ⇒ one would need
**380 in a single pass**.

⇒ ⭐ **The multiplier of R10-A3 is real, but it is the number of ATTACHED TENANTS, not of logind
sessions.** The loop makes one call **per session served**, and that is the count that
grows.
`[?]` **The low end cannot be measured on this machine**: there is a **floor of 63 sessions** in
`linger` that belong to the other benches.

#### ⭐⭐ And the half that counts: **the latency arrives long before the eviction**

`[M]` With **one single** tenant:

| guardian slow by | fps | median latency | p95 | **triggers** |
|---|---|---|---|---|
| — (0) | **39.78** | 9.9 ms | 11.5 ms | 0 |
| **1 000 ms** | ⛔ **20.85** | 11.3 ms | **77.3 ms** | ⭐ **0** |
| **2 000 ms** | ⛔ **1.90** | 31.9 ms | ⛔ **2 028 ms** | ⭐ **0** |

⇒ ⛔⛔ **One single tenant with a one-second guardian loses HALF of the frames, and nobody gets
detached.** At two seconds the desktop is unusable — **still zero evictions**.
⭐ **It is the defect that bites as LATENCY long before it bites as eviction**, and it is the shape that
`CODER.md` §1-bis says weighs more than frames.

#### ⭐⭐⭐ The surface with several tenants — **and the damage arrives WITHIN the tolerance the code allows itself**

`[M]` 30 s per cell, under the lock:

| N | D | **P = N×D** | calls per pass | fps per session | p95 | **triggers** |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 1 | 39.50 | 11.5 ms | 0 |
| 1 | 1000 | 1000 | 1 | 21.42 | 78.0 ms | 0 |
| 1 | 2000 | 2000 | 1 | 1.84 | 2 036 ms | 0 |
| **3** | 0 | 0 | ⭐ **3** | 37.4 / 37.6 | ~11.7 ms | 0 |
| **3** | **333** | 999 | ⭐ **3** | ⛔ **20.8 / 20.6** | ~34 ms | ⭐ **0** |
| **3** | 667 | 2001 | ⭐ **3** | ⛔ **1.77 / 1.87** | ~2 014 ms | ⭐ **0** |

Three things now established **by measurement instead of by deduction**:

1. ⭐ **The pass costs exactly N calls**: `[M]` **48 calls in 30 s at N=3** against **16** at
   N=1. The blocked time is **N × D**, linear in the tenants — **as the finding said**;
2. ⭐⭐ **What governs the damage is `P = N×D`, not D**: N=3 with D=333 and N=1 with D=1000 give **the same
   ~21 fps**; N=3 with D=667 and N=1 with D=2000 give **the same ~1.8**;
3. ⛔⛔ **And the damage arrives WITHIN the tolerance the code allows itself**: at **D = 333 ms** — that is
   **just above the 300 ms that `sentinella.c` itself budgets for logind** — **three tenants
   already lose half of the frames**, ⛔ **and the product says nothing, because it detaches nobody.**

#### ⭐⭐⭐ The frontier **narrows as 1/N**, and cuts what the code already allows **at four tenants**

| N | D that **halves** the rate | against the **300 ms** `sentinella.c` budgets |
|---|---|---|
| 1 | 1 000 ms | well above |
| 3 | 333 ms | **on the edge** |
| **5** | ⛔ **200 ms** | ⛔ **BELOW** |

⇒ ⛔⛔ **Around four tenants, the tolerance the product allows itself is enough to
halve everyone's rate.** And `[M]` the calls per pass are **1 · 3 · 5 · 7** at N = 1/3/5/7:
**linear, measured**.

⛔⛔⛔ **And the case that closes it**: `[M]` at **N=7 with D=286 ms — that is exactly that budget — EVERY
desktop collapses to ~1.3 fps with a p95 of two seconds, and not one line is written**, because
nobody is detached. Already at **half** the budget (143 ms) **40 %** of the frames go.

`[M]` **Twenty cells, N from 1 to 7**, and the product `P` governs the damage while its composition is
irrelevant: at P = 1000 → 21.4 · 15.2 · 14.2 · **12.3** fps; at P = 2000 → 1.84 · 1.82 · 1.21 ·
**1.26**.

#### ⚠⭐ And finding R10-A3 must be **corrected where it exaggerated**: eviction **is not the normal outcome**

`[M]` **Zero dead-line triggers in ALL TWENTY cells**, N from 1 to 7, P up to **5 001 ms**.
⇒ The eviction was reproduced **once**, with the exact deduced signature, ⛔ **but only as a
TRANSIENT**: a stage that **starts** producing while the loop was **already** blocked.

⭐ **What R10-A3 gets right is the mechanism and the linearity; what it overestimates is eviction as the
ordinary consequence.** ⛔ **The ordinary consequence is SILENT degradation** — and for `CODER.md`
§1-bis that **weighs more than frames**.

`[?]` **Damage that survives its cause**: two sessions stay at **7-9 fps with 200-270 ms**
of latency **while the guardian is at zero and their scenes are drawing**. Not explained, and reported as an
**observation** — ⭐ and it is the reason these reports must be read **per session**, not as an
average.

#### ⭐ And a product finding found by mistake

⛔ **With the slow guardian a new tenant cannot connect at all**: the handshake
expires. ⇒ It is not that it slows down whoever is already inside: **it closes the door on whoever arrives**.

⚠ And a side defect, already named: **`sentinella_conti()` has no caller in `src/`**.
It is the counter the header declares it put in so that the choice of querying logind
**synchronously** could be **re-measured instead of believed** — ⛔ and today nobody emits it.

### 6.14 ⭐⭐⭐ THE HARD CASE IN BYTES — **the discrepancy is resolved: the 44.6 was true**

`banchi/10-b90-filo.py` extended (+ `10-b90-firefox.sh`), `[M]` 25 Aug 2026, 2560×1080, H.264, 30 s,
under the lock.

#### Where the 44.6 came from — read, with the quotation

| | |
|---|---|
| **the scene** | the *«film con la GRANA»*: the user's scene with `noise=alls=30` ⇒ `[M]` VP8, 2560×1080, 30.3 fps, **58.2 Mbit/s of source**. **It is noise: every pixel changes every frame** |
| **the meter** | the *«carico video»* column was **the payload bytes and nothing else** — no QUIC, ACK, retransmissions, audio. ⚠ The column comparable with today's meter is *«filo `lo`»*, **48.42** — ⛔ **which WORSENS the discrepancy**: against 4.478 it makes **eleven** times |
| **the cures** | ⛔ **OFF**: in phase 9 they were born off (**I6**), they became defaults **on 24 Aug** |
| ⭐ **the player** | **firefox-esr** with the page stretched over the canvas; phase 10 uses `mpv --fullscreen` ⇒ **two different images of the same file** |

#### `[M]` The re-measurement — **four arms, one variable at a time**

| arm | scene | player | cures | mean on the wire | payload | bytes/fr |
|---|---|---|---|---|---|---|
| A1 | grain | firefox | off | 2.427 | ⛔ 0.000 | ⛔ **0 frames** |
| ⭐ **A2** | grain | mpv | off | **51.506** | **46.931** | 263 427 |
| A3 | grain | mpv | **on** | 49.627 | 47.209 | 266 132 |
| A4 | hard | mpv | on | 9.647 | 8.990 | 37 420 |

⭐⭐⭐ **The two measurements AGREE**: A2 against phase 9 §14.2 — payload **46.931 against 44.574**
(1.05×), wire **51.506 against 48.42** (1.06×), bytes/frame **1.10×**. ⇒ Another day, another bench,
another meter: **6 %**.
⇒ ⛔ **There is nothing to correct** in `CODER.md` §1-bis nor in `DECISIONI.md`: **the 44.6 was true.**

**How the eleven times divide up**: ⛔ **not the cures** (0.96×, they remove 4 %) · ⭐ **the scene,
5.1×** — the «hard» one compresses **five times better** than pure grain · ⚠ **and 2.2× belongs to §6.3
itself**.

> ##### ⚠ ⛔ AND THIS CORRECTS §6.3 — the anomalous number was its own
>
> `[M]` A4 gives **9.647 Mbit/s and 37 420 bytes/frame** where §6.3 gave **4.478 and 16 884**, on the
> **same scene, same cures, same product**. ⭐ And the 37 420 **find again the 37 081** that a
> phase 9 tool had already written. ⇒ **The number to look at with suspicion is the one of §6.3.**
> ⚠ *The conclusion of §6.3 — «il filo non è il vincolo» — **does not change**: what changes by a factor of two is the
> cost of the hard scene.*

#### ⭐ The REAL worst case — eight scenes, **no average**

| scene | entropy | mean on the wire | peak | bytes/fr |
|---|---|---|---|---|
| ⛔ **noise** (pure random) | yes | ⛔ **225.0** | **315.3** | **1 555 098** |
| grain (phase 9) | yes | 49.6 | 65.0 | 265 957 |
| fractal | yes | 18.9 | 24.2 | 74 340 |
| Conway | yes | 12.5 | 29.7 | 49 068 |
| hard | yes | 9.9 | 47.5 | 38 609 |
| **real desktop** | — | **0.53** | 0.86 | 1 873 |
| ⛔ flag | **UNMASKED** | 0.48 | 0.53 | 250 |
| ⛔ **scrolling text** | **UNMASKED** | 0.37 | 0.38 | ⭐ **87** |

**The row that closes it**: worst case **225 Mbit/s per session** ⇒ **×10 = 2 250** (3 153 at peak)
against the wire `[M]` measured at 11 900 ⇒ ⭐ **the wire is not the constraint even so** — ⚠ **but the
margin is 5×, not 200×**.
⛔⛔ **And against `--tetto-banda-mbit` it is 1 125 % on its own**, with the static that lives **in the child** and
**no aggregate counter in the whole of `src/`**: ten children pay it ten times (§3.5).

#### ⭐ The three things nobody expected

1. ⭐⭐ **Dense scrolling text costs 87 bytes per frame — TWENTY-TWO TIMES LESS than a still
   desktop** (1 873). Motion vectors eat up a uniform scroll. ⇒ *«Il caso che
   l'utente fa davvero»* is **the easiest scene of the bench**, and it had been chosen as hard.
2. ⚠ The number of §6.3 on the hard scene, corrected above.
3. ⛔ **A bench defect that turned out well**: the needle looking for the state of a cure took **the last
   line** naming it, and with the cures on there are **two** ⇒ *IGNOTA* on a cure very much on,
   and the bench **refused to measure two arms out of four**. ⭐ **Red on a healthy product,
   noisy: it is the right direction in which to be wrong.**

#### The `[?]`

⛔ **The phase 9 player cannot be redone**: A1 puts Firefox back line by line and gives **0 frames in
30 s** — ⚠ **Firefox is broken on that machine for everyone** (phase 9 §20.1-ter, and **it is not ours**)
⇒ the ratio of A2 to the 44.6 comes out marked `[?]` **conditional**, never `[M]`: the argument is that the
film is **as big as the canvas**, so the two players show the same pixels without scaling —
⭐ **an argument, not a measurement** · **the player pays on the same GPU**: the 17.6 fps of the noise are partly
**contention with the decoder**, not separated · ⚠ **it is the SYNTHETIC worst case**: phase 9
measured the grain with the real browser at **21.5-23.1** Mbit/s, **half** of the bench ⇒ these are an
**upper bound**.

⭐ And two scenes that had been chosen as hard were **unmasked by the bench itself**
(§1.30): the flag and **the scrolling text**.

### 6.15 ⭐⭐⭐⭐⭐ IL MECCANISMO DEL DIRUPO — **non cade sul numero di sessioni: cade sul carico di composizione**

`banchi/10-b9d-dirupo.py` (+ `10-b9d-chi-tiene-la-gpu.py`, `10-b9d-conti.py`,
`10-b9d-dove-sono-fermi.py`), `[M]` 25 agosto 2026, scena satura 1080p, gradini da 40 s, sotto
lucchetto.

#### ⭐⭐⭐ La prova: **stessa popolazione, cambia solo quante scene disegnano**

Otto sessioni, otto desktop, otto figli — **sempre gli stessi**:

| gradino | scene che **disegnano** | disegni/s | GPU render | GPU **video-enhance** | fot/s a testa |
|---|---|---|---|---|---|
| 7S | 7 | 420 | 99,3 % | 48,7 % | **33,6** |
| ⛔ **8S** | **8** | **459,8** | 99,6 % | ⛔ **0,4 %** | ⛔ **1,6** |
| ⭐⭐ **7S+1F** | **7** | 421 | 99,4 % | **46,7 %** | ⭐ **33,4** |
| 6S+2F | 6 | 360 | 81,9 % | 18,5 % | 39,2 |
| **8S** (àncora, rifatto in coda) | 8 | — | — | — | ⛔ **1,6** |

⭐⭐⭐ **`7S+1F` è la prova**: si **spegne una scena** e il ritmo torna **da 1,6 a 33,4 fot/s**, senza
toccare **né sessioni, né desktop, né figli**. E rimettendo le scene sature il dirupo **si
riproduce**: ⭐ **reversibile e ripetibile.**

⇒ ⭐⭐ **Il confine cade fra 873 e 953 Mpixel/s composti** — e **combacia col soffitto della
composizione misurato per un'altra strada in §6.11: 0,97 Gpixel/s.**
⇒ ⭐⭐⭐ **La grandezza è CONTINUA, e il prodotto la sa calcolare.** Il dirupo non è un numero di
sessioni: è una **soglia su quanto si sta componendo**.

> ##### ⭐⭐⭐ E la grandezza giusta sono i **PIXEL**, non i fotogrammi — la refutazione interna
>
> `[M]` Il braccio **`6S+2W`** (due scene ridotte a 960×540) fa **480 disegni al secondo** — cioè
> **più** dei 460 del gradino che crolla — ⭐ **e non crolla**, perché quei disegni sono più piccoli:
> **808 Mpixel/s** contro 954.
> ⛔ **Né serve l'occupazione**: `render` è al **99,2 %** nel braccio **sano** e al **99,5 %** in
> quello **crollato**. ⇒ ⭐⭐ **L'occupazione satura e SMETTE DI INFORMARE; a discriminare è la
> DOMANDA.** È `LEZIONI.md` §1.34 un'altra volta: la colonna che avvisa non è quella dell'altra volta.
> ⚠ **Senza quel braccio sarebbe stato riferito il numero sbagliato** — una soglia in fotogrammi
> invece che in pixel.

#### ⭐⭐ Perché è un dirupo e non una discesa — **la colonna che lo dice è `video-enhance`**

`[M]` `remotix` sul motore **render**: **0,00 %**. Il render è **tutto di `gnome-shell`** — **99,52 %**
al gradino 8. ⭐ (Conferma §6.11: **la nostra conversione sta sul VEBOX**.)

⇒ Quando i compositori prendono il **100 %** di `rcs0`, **la cattura non riceve più fotogrammi**:
`video-enhance` crolla da **48,7 % a 0,4 %**, cioè ⛔ **il codificatore non ha più niente da fare. Non
rallenta: si ferma.**
`[M]` Le consegne del palco al padre passano da **39 a 2 fot/s** — ⭐ **letti dal padre**, non
ipotizzati.

⇒ ⛔⛔ **Il collo non è nel padre e non è nel codificatore: è A MONTE, nella composizione.**

#### ⛔ Cinque piste su sei sono **FALSE** — e dirlo vale quanto trovare la vera

| pista | verdetto al gradino del dirupo |
|---|---|
| **ripiego in software** | ⛔ **falsa** — `[M]` **zero** ripieghi, tutti su `renderD128` |
| **un'attesa che diventa il ritardo di tutti** | ⛔ **falsa** — zero chiamate lente, e la CPU del padre è **0,0 nuclei** |
| **la soglia della coda** (`--sgombra-soglia-ms`) | ⛔ **falsa** — `[M]` coda sopra **0**, sotto **0**, abbandoni **0** |
| **il regolatore del ritmo** | ⛔ **falsa al gradino 8** — `[M]` scende **0**, risale **0** |
| **il ciclo del padre / logind** | ⛔ **falsa** |
| ⭐⭐ **l'aritmetica dei buffer** — *la pista che sembrava la migliore* | ⛔⛔ **FALSA, e refutata da chi l'aveva proposta**: `[M]` il produttore ne dà **8**, non 6 ⇒ soglia **100 ms**, e ne teniamo **30,4** — **×0,30**. ⭐ **Non restiamo mai senza buffer** |

⭐⭐ **E i due bracci di controllo chiudono le due piste che restavano**: `[M]` con
`--sgombra-soglia-ms 0` il dirupo è **identico** (1,46-2,08 fot/s); con `--niente-ritmo-adattivo`
**identico** (1,48-2,76), e al gradino 8 `non_partiti = 0`, discese **0**, abbandoni **0**.
⇒ ⛔ **Nessuna delle due cure della fase 9 causa il dirupo.**

⭐ **E il testimone dice dove stanno fermi i figli**: al gradino del dirupo, `ioctl` su `/dev/dri` al
**100 %** dei campioni, ⛔ **`sendto` allo 0 %** ⇒ **nessuna contropressione del padre**. E cresce col
carico: `[M]` **0 % (5S) → 10 % (6S) → 28 % (7S) → 38 % (8S)**, e **22 % appena si spegne una scena**.

⇒ ⭐⭐ **La catena, per intero**: otto compositori saturano `rcs0` → il `vaSyncSurface` del VPP
(`codificatore.c` · `converti_sulla_gpu()`) non torna → il figlio resta dentro l'`ioctl` DRM → la cattura non consegna →
⛔ **il codificatore non riceve più niente**. ⭐ E *«`GPU video` che crolla»* era **il sintomo giusto,
letto al contrario**.

#### ⛔⛔⛔ E un difetto di prodotto trovato per strada, che **non era il bersaglio**

`[M]` A **cinque** sessioni, **cinque client sono stati sfrattati in 1,3 s**:

```
ritmo …: arretrato LETTO 40 volte, massimo 2, ultimo 2, posti 2
  — 40 fotogrammi NON PARTITI in questo secondo, 444 in tutto
linea-morta … causa=silenzio usciti_byte=0 coda_video=10443
  silenzio_ms=10997 persi=0
```

⇒ ⛔ **`arretrato` resta incollato al tetto dei posti del regolatore**, che blocca **OGNI** fotogramma;
`usciti_byte=0`; il client **non ha più niente da riscontrare**, tace; e **la linea morta lo sfratta
con `persi=0`**.

⭐⭐ **È un ANELLO CHIUSO fra due cure della fase 9** — la stessa famiglia di S.4, ⛔ **ma qui su una
coda mordente, cioè su utenti che stanno lavorando.**
⭐⭐⭐ **E i due bracci lo confermano da due strade indipendenti**: `[M]` spegnendo **l'una O l'altra**
cura, **8 sessioni su 8 sopravvivono** e i fotogrammi non partiti vanno a **zero**. ⇒ **Non è una
coincidenza: è un anello, e si apre togliendo un anello qualsiasi dei due.**

⚠ **E lo sfratto ha rotto metà del giro**: al gradino 8 ricevevano **3 client su 8**. ⭐ **Il che
rafforza la conclusione**: il dirupo è arrivato lo stesso, con **tre** client e **otto** compositori
— cioè **non dipende da quanti guardano, ma da quanti disegnano**.

#### I due difetti del banco, trovati e curati

1. ⛔ `aggregato()` tornava `None` appena una sessione mancava — *«un totale con un buco non è un
   totale»*, giusto in astratto — ⛔ ma con cinque sessioni sfrattate **ogni** gradino aveva un buco,
   il verdetto «DIRUPO» **non è mai uscito**, e **il pilota ha saltato i due bracci di controllo**
   dicendo *«non ho ritrovato il dirupo»* **mentre il dirupo era sotto gli occhi**. ⇒ Ora il confronto
   è **appaiato**: le stesse sessioni prima e dopo, col loro numero **dichiarato**.
2. Il conto delle serie pretendeva un figlio per sessione **dichiarata**, non per sessione **viva** ⇒
   ⭐ si è rifiutato di dichiarare (`None`, mai un numero plausibile).

`--certifica`: **71 casi su 71**.

### 6.16 ⭐⭐⭐⭐⭐ LA SCENA MISTA — **il tetto è una FUNZIONE, e i costi si sommano**

`banchi/10-b98-mista.py` (2 527 righe; importa `10-b92-dieci.py` e ⭐ **non ne modifica una riga —
diff vuoto**), `[M]` 25 agosto 2026, 1080p H.264, gradini da 30 s a regime, undici utenti veri, sotto
lucchetto, ⭐ **palchi orfani verificati PRIMA di sgomberare** (zero su tutti e undici).

#### ⭐⭐⭐ Il costo di una sessione sul motore che fa da collo — e **si sommano**

| ruolo | GPU `render` | byte/fotogramma |
|---|---|---|
| **satura** (schermo intero) | **14,4 %** | 5 600 |
| **desktop vero** (finestra + due finestre vere) | **10,7 %** | 4 650 |
| **ferma** | ⭐ **0,01 %** | 266 |

⭐⭐ **E i costi si SOMMANO, anche fra ruoli diversi**: `[M]` 1S **14,4** · 2S **28,8** · 3S **43,4** —
lineari, **non si ostacolano**. E tre sature più tre desktop veri: **75,3 % previsto contro 75,6 %
misurato — scarto 0,4 %.**

⇒ ⛔ **L'ammissione non deve contare sessioni: deve SOMMARE LAVORO.** E 100 / 14,4 = **6,9** sature —
⭐⭐ **mentre §6.5, misurata da un altro banco e per un'altra strada, dice «fino a sei nessun graffio,
la settima rompe»**. Due banchi indipendenti, stessa conclusione (`LEZIONI.md` §1.28).

#### `[M]` Dieci ferme accanto a una che lavora: **non se ne accorge**

| | 1 satura sola | + 10 ferme | doppia durata (60 s) |
|---|---|---|---|
| fot/s di chi lavora | 39,50 | ⭐ **39,59 (+0,2 %)** | 39,65 |
| ritardo mediano | 9,9 ms | ⭐ **9,7 ms** | 9,7 ms |
| chiavi | 0 | **0** | 0 |
| GPU `render` macchina | 14,5 % | ⭐ **14,5 %** | — |
| CPU (20 nuclei) | 6,1 % | 7,7 % | — |
| PSS totale | 295,7 MiB | ⛔ **2 044,8 MiB** | — |

⇒ ⭐ **Di GPU, zero.** ⛔ **La sola risorsa che un inquilino fermo consuma è la MEMORIA** — ed è quella
a porre il vero tetto sulle ferme (31 GB ⇒ `[?]` ~170), non la scheda.
⭐ E `LEZIONI.md` §1.32 regge: a durata doppia **39,65** contro 39,59 — **il giro corto non
sottostimava**.

#### ⭐ E la scena realistica ne fa stare **PIÙ** di quella uniforme

`[M]` **Tre sature + tre desktop veri + due ferme = otto sessioni, sei delle quali lavorano davvero**:
tutte a **36,4-38,1 fot/s**, ritardo **9,5-13,8 ms**, zero chiavi, `render` **75,6 %**. Le due ferme
aggiunte sopra: 75,6 → **75,8 %**.
⇒ Il desktop vero costa **il 26 % in meno** di una satura ⇒ **la scena vera regge dove quella uniforme
cedeva alla settima**.

#### ⛔⛔⛔ Il colpo di scena: **IL RISVEGLIO SIMULTANEO**, e un budget preso all'ingresso non lo vede

`[M]` Una satura + **otto ferme**, le otto scene accese **in 19 ms**:

| | prima | dopo |
|---|---|---|
| chi lavorava già | **39,36 fot/s** · ritardo **9,7 ms** | ⛔ **1,60 fot/s** · ritardo **756 ms** (p95 997) |
| `render` della macchina | 14,3 % | **88,2 %** |
| GT / RC6 | 0 MHz / 66,7 % | 1550 MHz / 8,9 % |

⇒ ⛔ **Chi lavorava perde il 95,9 % del ritmo, e il ritardo fa ×78.** Otto sessioni ammesse quando
costavano `[M]` **0,01 % l'una** si svegliano insieme e ne chiedono **8 × 14,4 = 115 %**, più il
titolare: ⛔⛔ **il 130 % di un motore che ne ha 100.**

⭐⭐ **E le due colonne raccontano cose diverse** (`LEZIONI.md` §1.34): il **RITMO** (sintomo) crolla
**dentro il primo intervallo del metro — cioè entro 2 s, sotto la sua risoluzione**; il **RITARDO**
(meccanismo) sale **gradualmente**: 154 → 420 → 606 → 805 → **1 004 ms**, e si assesta dopo **8-10 s**.

⭐ `[M]` **L'apertura di una sessione non peggiora mai col numero**: 2 054-2 223 ms, e l'undicesima si
apre come la prima.

⭐ **E lo sfratto di §6.3 NON è scattato**: `[M]` dieci ferme sono **sopravvissute a tutta la salita**.
⇒ Quell'eviction **non è incondizionata**, e il banco sa distinguere **un cliente morto da uno fermo**
— che sul filo danno lo stesso zero.

#### I guasti innestati — **50 casi, 0 rossi**, ciascuno girato

Ferma che si muove (orologio ⇒ smascherata dal **ritmo**; salvaschermo ⇒ dalla **seconda** colonna) ·
scena a nome di una ferma ⇒ rosso **anche col filo muto** · satura che non satura · ⭐ **satura
AFFAMATA a 1,5 fot/s che NON è «non satura»** · conto letto dal gradino prima · risveglio che non
avviene / parziale / con le ferme già sveglie / **col cliente morto** · ⭐ **risveglio affamato che è
comunque un risveglio** · metro del «quanto ci mette» **tarato su un crollo iniettato a 6,0 s** più
due controlli negativi · delta GPU su platea che cambia · comando del risveglio validato con `bash -n`
**prima**, dove non costa niente.
⛔ **E la suite di `10-b92` rifatta girare alla fine: uscita 0.**

⭐ **E i «non giudicati» sono quasi tutti il banco che si rifiuta dove una sessione ferma non può
produrre una mediana del ritardo — quel rifiuto *è* la misura della quiete.**

#### ⛔ I tre difetti del banco, e uno **è passato a un pelo**

1. ⛔⛔ **il `pkill` globale ereditato**: `[M]` a fine giro trovava **24 clienti vivi di un altro
   banco** — quello che aveva appena preso il lucchetto. **Non li ha uccisi solo perché aveva
   sgomberato prima che nascessero**, e ⛔ **la cura era già scritta in §6.3**;
2. ⛔ **una chiave di riduzione copriva il «misurato»** di un banco importato ⇒ `ha_misurato()`
   sempre falso e **quattro predicati muti INSIEME**, senza un rosso né un giallo. ⭐ Trovato
   **rileggendo**, non da un rosso;
3. ⛔⛔ **«svegliata» giudicata sul RITMO invece che sulla sollecitazione**: le otto si erano svegliate
   benissimo (fotogrammi da ~5 kB, **18 volte** i 266 B di una ferma) ma consegnavano 1,5 fot/s,
   **sotto la soglia delle ferme** ⇒ il banco si è rifiutato di misurare **proprio la scena che
   esiste per misurare**. ⭐ Ha detto *«non ho misurato»* e non *«nessun effetto»* — ⚠ **ma il ritmo
   basso non era il contrario del risveglio: era il suo RISULTATO.**

#### Le `[?]`

⛔⛔ **A quante ferme svegliate insieme comincia il crollo**: misurato **otto** (crolla); fra una e
otto **non si sa dov'è il ginocchio** — ⭐ **ed è il numero che servirebbe a tarare un budget contro
il risveglio** · ⛔ **due sature + N ferme**: solo N=0, la scala non è stata fatta — **i turni di
lucchetto sono finiti prima** · ⚠ *«a strappi»* qui è **una finestra, non un'intermittenza**, e il
motivo è dichiarato in testa al banco: un ciclo acceso/spento farebbe vedere la scena «ferma» mentre
lavora, **cioè proprio l'errore che il banco esiste per chiudere** · ⚠ le occupazioni sono **tempo
occupato**, e la GT si muove da 0 a 1550 MHz ⇒ **l'88,2 % del risveglio non è il 130 % della domanda**.

---

## §7 · ⛔ Che cosa NON ha funzionato

### 7.1 Il conto degli errori di banco — **ventidue**, e la forma è sempre la stessa

⛔ In un giro solo, i dieci banchi hanno prodotto **ventidue difetti di banco**, e ⛔⛔ **quasi tutti
tacevano invece di dare rosso** — la forma che `LEZIONI.md` §1.29 aveva chiamato per nome due giorni
prima, e che si ripresenta identica.

| banco | i difetti pagati |
|---|---|
| **i dieci** (§6.5) | ⛔ **nove, e otto su nove tacevano**: `pgrep -f` che trova sé stesso (ogni sessione sarebbe risultata «viva» per sempre) · percorso di fuori invece che di dentro il contenitore · il contatore di `lo` **che non era il suo** (22× più grande) · la scena che **non mordeva** · `drm-engine-capacity-video: 2` letto **come nanosecondi**, tetto 100 invece di 200 · il delta GPU su una platea di contesti **che cambia** (−76 %) · `misura()` che sovrastimava di 1/(N−1) · i processi di `enable-linger` scambiati per **palco orfano** |
| **il filo** (§6.3) | `wc -l < file` in coda a `sudo -S` ⇒ `None` silenzioso · `$1` di `awk` espanso da `bash -c` ⇒ campo vuoto · graffe di `nft` prese da bash · `ss -uanp` che **non vede** le porte del cliente di prova · l'ICMP che senza contatore proprio finiva sotto **«vicini»** |
| **la tabella piena** (§6.4) | il `tail` che **perdeva** la riga sotto migliaia di righe · la scena spenta **prima** dei clienti (àncora spostata di **42 s**) · `pgrep -f` che contava **7** figli dove ce n'erano 3, poi **0** · ⛔ **`pkill -f` che uccide la shell che lo sta eseguendo** ⇒ la prova dopo partiva **contro dei fantasmi** |
| **il terreno** (§1.4) | ⛔ il predicato più importante che diventava **IGNOTO** invece di guardare la scheda nominata (forma E8) · `bash -c "…; sleep N # segno"` che **perde il segno** ⇒ il guasto restava innestato e chi l'aveva messo **credeva di non averlo messo** |
| **il costo** (§6.4-bis) | ⛔ la soglia sui **byte per fotogramma**, che ordinava i due estremi **al contrario** (forma E15) |

⭐ **E due li ha evitati un banco d'altri**: la capacità **2** e il §CLOCK, che il metro tarato di §6.1
portava già scritti. ⇒ **Un metro tarato non serve solo a chi lo scrive.**

### 7.2 ⛔ Le prove che non si sono potute fare, e perché

| | |
|---|---|
| **HEVC nel saturatore** | misurato **solo H.264** (§6.2). Il banco lo fa; le due colonne resterebbero **separate, non mediate** |
| **la rete vera nella salita a dieci** | i clienti giravano sulla **stessa macchina**, su `lo` (MTU 65536) ⇒ il budget di rete della salita è **contato, non provato** (§6.5) |
| **tre sessioni video insieme** sul filo stretto | ⛔ **la linea morta le sfratta prima che il riproduttore dipinga** (§6.3) |
| **il modo QVBR**, che è quello che il prodotto usa | misurati CQP e CBR, i due estremi verificabili senza ambiguità (§6.6) |
| **l'immagine** | nessun banco dice *«si vede peggio»*: ⭐ **quello lo dice l'utente**, ed è §10 |

### 7.3 ⛔⛔⭐ IL DIFETTO ERA NELLO STRATO CHE CI COORDINA — *«silenzio invece di rosso», un piano più su*

*Secondo giro, 24 agosto 2026.* Il lucchetto della GPU di §1.1 ha retto il suo mestiere — ⭐ nessuna
misura è stata falsata da un vicino, e i banchi lo dichiarano invece di dedurlo. ⛔ **Ma il modo in
cui si aspetta il turno era rotto, e rotto nella forma che questa fase ha imparato a riconoscere.**

#### ⛔ `prendi()` non è una coda: è una **corsa**

`[M]` Il `mkdir` si ritenta ogni 5 s e vince **chi arriva per primo dopo un `molla`**: nessuna
prenotazione, nessuna anzianità. Con **cinque** incarichi sulla stessa scheda e turni da ~90 minuti,
un banco che aspettava da **due ore** ha **perso due passaggi di mano consecutivi** senza mai toccare
la GPU.

⛔⛔ **E il danno non è il ritardo: è che il giro veniva SALTATO sotto un codice d'uscita che
somigliava a un problema di terreno.** ⇒ La domanda **non veniva mai posta**, e chi leggeva l'esito
vedeva un guasto invece di un buco. È esattamente la forma di `LEZIONI.md` §1.29 — *silenzio invece
di rosso* — **un piano più su**: non nel banco, in quel che coordina i banchi.

#### ⭐⭐ La cura: **«il turno non è arrivato» è un esito suo**, e solo lui si rimette in coda

| uscita | vuol dire | si rifà? |
|---|---|---|
| 0 / 1 | ⭐ **un giudizio** — regge / non regge | ⛔ **mai** |
| 3 | *«non giudico»* — ha misurato, e qualche predicato non ha potuto parlare | ⛔ **mai** |
| 2 | il terreno non regge, o l'uso è sbagliato | ⛔ mai — **un terreno cattivo si GUARDA**, non si ritenta finché per caso passa |
| **4** | ⭐ **il turno non è mai arrivato** — la domanda non è stata posta | ✅ **sì, fino a quattro volte** |

⛔⛔ **E il `3` NON si rimette in coda, di proposito.** È il più tentante — *«qualche casella non ha
giudicato, riprova»* — ed è ⭐ **la strada esatta per misurare due volte finché esce il numero che
piace**. In un progetto che ha ritirato due conclusioni per questa ragione, la tentazione si chiude
con una regola, non con la buona volontà.

⭐ **E la logica è stata provata contro un banco finto** che esce coi codici scelti apposta — perché
*un pilota che sembra giusto e non è mai stato visto rimettere in coda ha lo stesso difetto che sta
curando*: `4,4,4,0` ⇒ quattro chiamate, esce 0 · `1` ⇒ una chiamata · `0` ⇒ una · `3` ⇒ una · `2` ⇒
una · sempre `4` ⇒ si ferma dopo quattro **e lo dice**.

#### ⛔ E tre trappole del mestiere, tutte pagate da più di un banco

1. ⛔⛔ **In bash i `trap` sono RIMANDATI finché un figlio in primo piano non finisce.** ⇒ Un SIGTERM
   al pilota sarebbe restato **in sospeso per tutta la durata del giro**: lucchetto occupato, campo
   sporco, **e nessuna riga rossa** — si vedeva solo un pilota che *«non risponde»*. ⚠ La forma nota
   era *«SIGTERM ammazza senza far girare il `finally`»*; **qui era peggio: non ammazzava,
   addormentava la cura**. Il figlio va messo in fondo e atteso con `wait`.
2. ⛔ **Una trappola che chiama una funzione definita più avanti «sembra armata»**: `molla: comando
   non trovato`, e la pulizia non avviene. ⇒ **Peggio di nessuna trappola.**
3. ⛔⛔ **`pgrep -f` / `pkill -f` acchiappano la riga di comando che li esegue.** `[M]` **Due**
   incarichi si sono **uccisi il proprio pilota** credendo di controllarlo, e uno se n'è accorto solo
   perché il PID restituito era quello della shell che lanciava. ⇒ Il PID dev'essere **quello che il
   pilota ha scritto di sé**, e i modelli si scrivono `campagn[a].sh`. ⚠ **La cura era già scritta in
   questo progetto** (`10-b92-dieci.py`, `cerca_giornale`) e non era stata applicata.

⭐ **E una cosa fatta bene, che vale la pena tenere**: un pilota ucciso a metà ha **scritto i numeri
prima di sgombrare**, chiuso i palchi dei suoi sette utenti, e poi — *«il lucchetto adesso è di
`10-b5`: non lo tocco»* — **si è rifiutato di rilasciare un lucchetto che nel frattempo era diventato
di un altro**.

#### ⛔⛔⛔ E il difetto peggiore del lucchetto: **si può aspettare SÉ STESSI**

`[M]` Un banco ha trovato il campo intestato al **proprio** nome con 4 801 s residui, mentre il suo
pilota ne chiedeva 2 120: ⇒ non era lui, era **un'istanza morta prima che la trappola di pulizia
esistesse**.

> ⛔⛔ **`prendi()` non ha nessun ramo per «il lucchetto è GIÀ MIO»**: se il nome dentro combacia col
> proprio, aspetta esattamente come se fosse di un altro.

⇒ **Un pilota morto male lascia il lucchetto col proprio nome, e il pilota successivo aspetta sé
stesso fino alla scadenza.** `[M]` **Ottanta minuti di GPU bloccati per tutti e cinque**, e ⛔ **nessuna
riga rossa da nessuna parte** — solo un pilota che *«sta aspettando il suo turno»*.
⚠ È la stessa famiglia della corsa, **e peggiore**: là si perde un passaggio, qui **si blocca la fila**.

⭐ La cura sta **nel pilota**, non in `09-lucchetto.py`, che è di tutti: se il nome è il proprio **e**
nessun processo proprio è vivo sulla macchina, **adotta** e rimette la scadenza — ⛔ **dichiarandolo**.
*Adottare in silenzio sarebbe peggio del blocco.*

#### ⛔ E la terza: **una scadenza sottostimata regala la GPU a metà misura**

Il lucchetto ha una scadenza apposta — chi la trova passata **scassina dichiarandolo**, ed è giusto:
altrimenti un pilota morto bloccherebbe tutti fino a domani. ⛔ **Ma il rovescio non era stato
pensato**: un giro che dura **più** di quanto ha dichiarato si vede togliere la GPU **a metà
misura**, e chi la prende misura **su sette palchi vivi credendo la macchina sgombra**.
⇒ ⛔⛔ **Nessuno dei due vede rosso, e tutt'e due leggono numeri plausibili.**

⭐ La cura è la regola dell'asimmetria di `LEZIONI.md` §1.33, applicata alla durata: il tempo di
possesso si **somma dalle parti vere** del giro e si moltiplica per un margine **dichiarato** — `[M]`
63 minuti stimati, **101 dichiarati**, con tutt'e due stampati — perché *sbagliare in alto costa al
prossimo qualche minuto, sbagliare in basso costa a tutti e due la misura*.

#### ⛔⛔ E la quarta, trovata **provando la cura**: **i corridori orfani**

Nel mettere a posto il modo di correre, un banco ha trovato `[M]` **due `python3` vivi da 2h05m e da
50m**: erano gli **aspettanti** di pilota che lui stesso aveva ucciso, ⛔ **e stavano ancora correndo
per il lucchetto vero a nome suo**.

⇒ Se uno avesse vinto, avrebbe tenuto la GPU per **3 640 s con nessuno a mollarla**; e per tutti gli
altri sarebbe stato **un lucchetto occupato da un nome VIVO**: ⛔ **nessun rosso, nessuno scassino,
solo attesa.**

⭐ **La causa**: la trappola di pulizia si armava **dopo** aver preso il lucchetto ⇒ chi veniva ucciso
**mentre aspettava** lasciava in piedi il proprio aspettante. Le tre cure — trappole armate **prima**
della corsa, il corridore che gira come figlio così la trappola lo raggiunge, e la pulizia che chiude
anche il corridore **remoto** — ⭐ **sono state provate sul caso che prima non era stato provato: il
segnale ricevuto IN ATTESA**, non durante la misura.

⭐ **E la corsa infittita paga**: `[M]` un ciclo `mkdir` a **0,5 s che gira sulla macchina di prova**
(dentro **una sola** connessione: ritentare da fuori costerebbe 100-200 ms di rete a tentativo e
lascerebbe **comunque** una finestra più larga del passo dichiarato) prende il lucchetto **47 ms**
dopo il rilascio, contro i fino-a-5 000 di prima.

#### ⛔⛔ E la quinta, che è **passata a un pelo**: una pulizia globale ereditata

Un banco aveva ereditato dal suo predecessore la riga di sgombero `pkill -f '…cliente… --cliente'`,
con un modello **globale**. ⛔ Ma quel nome di cliente è quello che usa **ogni** banco della fase, e in
questo giro **anche gli utenti sono condivisi**.
`[M]` **A fine giro quel modello combaciava con 24 clienti VIVI, tutti di un altro banco** — quello
che aveva appena preso il lucchetto e **stava misurando**.
⭐ Non li ha uccisi **solo perché aveva sgomberato prima che nascessero**.

⇒ ⛔ La cura era **già scritta in questa stessa fase** (§6.3: *«chiude SOLO le proprie sessioni»*) e
non era stata applicata. Adesso lo sgombero combacia solo con la **propria cartella di lavoro**.
⚠ **È la seconda volta in questo giro che una cura già scritta nel progetto non viene applicata da
chi ne aveva bisogno** — l'altra è la trappola di `pgrep -f`. ⭐ Il difetto non è la disattenzione: è
che **quelle cure vivono nei commenti dei banchi, e chi copia una riga non copia il riquadro**.

⚠ **E `setsid` non basta**: un pilota è stato ucciso a metà verdetto perché **la scadenza di una
chiamata si è portata via l'intero gruppo di processi**. La misura era già finita e il lucchetto già
mollato, ⭐ ma la forma che regge è **un'unità vera** (`systemd-run --user`), con il suo cgroup,
interrogabile — non un `nohup`.

#### ⛔⛔ E la sesta: **la cura dell'adozione può rubare il lucchetto a sé stessi**

⚠ Va letta insieme alla cura del riquadro precedente, perché **è il suo rovescio**. Un banco si è
trovato **due copie del proprio pilota vive** (il pilota di ritenta non faceva più `exec`, quindi il
file del pid teneva **la shell** e il figlio Python restava orfano). Tutt'e due si chiamavano allo
stesso modo, tutt'e due correvano per lo stesso lucchetto — ⛔⛔ **e la regola «rilascia se il nome
combacia» avrebbe fatto sì che la copia IN ATTESA, ricevendo un SIGTERM, rilasciasse il lucchetto
della copia CHE STAVA MISURANDO e le sgomberasse i palchi, a metà misura, senza che nessuna delle due
vedesse rosso.**

⭐ Tre cure, tutte provate: una guardia di **istanza unica** con `flock` (provata in tre stati); la
regola di rilascio che si fida **solo** di «l'ho preso io», non del nome; e il pilota che scrive il
pid **del Python** e gli inoltra i segnali — ⭐ verificato: TERM alla sola shell, **e il misuratore è
uscito con lei, senza orfani**.

⛔ **E un terzo difetto della stessa famiglia**: un giro interrotto **ha scritto il suo file senza i
numeri** — il `finally` salvava i risultati, ma la voce delle celle veniva assegnata **solo se la
funzione tornava** ⇒ cinque celle misurate hanno prodotto un file che diceva *«nessuna cella»*.
⭐ **Un file che esiste e non porta niente è peggio di un file che manca: sembra un risultato.**

#### ⚠ E due cose che il terreno ha insegnato in questo giro

1. ⛔ **Un `tail -40` sul verdetto del controllo del terreno taglia le righe che dicono PERCHÉ.** `[M]`
   Il terreno dava due guai e il pilota ne stampava solo la coda: **le due righe rosse stavano in
   cima**. ⇒ Su rosso si stampano **tutte** le righe rosse — un verdetto troncato è un verdetto muto.
2. ⭐ **E la guardia giusta per una misura di GPU non è «nessun `remotix` altrui»**, che con cinque
   banchi accesi non si avvera mai: è **nessun `remotix-figlio` altrui vivo**. `[M]` Un server **senza
   figli costa GPU zero** (§6.4-bis, RC6 al 100 %), quindi i vicini fermi non disturbano; ⛔ **un solo
   figlio altrui vivo sì**, e quello codificherebbe sulla stessa scheda, lucchetto o no.

---

### 5.8 ⭐⭐⭐⭐⭐ IL TESTIMONE CHE FA VEDERE — **e la prima immagine del desktop remoto**

*25 agosto 2026, dopo che il regista aveva smesso di provare.* ⛔ **È il pezzo che teneva chiusa la
fase**, e non era codice del prodotto: era **non saper guardare**.

`[M]` Quattro strade provate e **nessuna dava il quadro** — lo scatto interno del figlio
(`cattura.bgrx` **0 byte**), la fotografia dello schermo (⛔ GNOME non espone
`wlr-screencopy`), la tela della pagina via Marionette (⛔ **ogni riattacco buttava giù la sessione
RCP**), il conteggio dei fotogrammi (⛔ dice **quanti**, non **che cosa**).

⭐ **La quinta ha funzionato al primo colpo**: `banchi/10-f1-testimone.py` — il **cliente di prova**
prende i fotogrammi **dal filo** (`--video-scrivi`), `ffmpeg -update 1` decodifica **l'ultimo**, e
ne esce un PNG. ⚠ Si dichiara **dove guarda**: **dopo il filo, prima del decodificatore del
browser** — non sostituisce la tela, la **precede**.

#### ⛔ Tarato, perché un PNG nero e il desktop hanno la stessa faccia dal lato del codice

| controllo | `[M]` |
|---|---|
| ⭐ **positivo** | la marca di `04-b30-scena` ritrovata dal lettore certificato: giro **«f1-taratura»**, disegno **3783**, contrasto **0,997** ⇒ guarda **quel** desktop, in **quell'istante** |
| ⛔ **negativo, sul vero** | fondo a `#000000` ⇒ **quasi-nero**, accesi **0,00121**; e **sotto la barra di GNOME il fotogramma è nero byte per byte** (accesi 0,00000000, luma massima 1). ⭐ Il metro sente **un pixel su ottocento**, e il desktop vero sta **800 volte** più su |
| ⛔⛔ **il terzo esito** | sessione appena nata, palco che non ha ancora consegnato ⇒ ⭐ **«NON HO GUARDATO», uscita 3** — **non** «era nero» |
| ⭐ **non rompe chi guarda** | con uno spettatore già attaccato il testimone è stato **RESPINTO** (`congedo 0x0f`, *«lo sfratto NON è scattato»*), e ⭐ **lo spettatore è rimasto attaccato** |

⭐ **`--certifica`: 4 predicati, sano 4 → guasto 12 → risanato 4.** ⚠ E **due guasti hanno morso su
codice del banco stesso**: G8 dichiarava «tinta unita» uno schermo nero **con la marca sopra**
(contava i colori invece della frazione diversa dal fondo); G12 aveva la barra finta **troppo
grossa** e passava per il motivo sbagliato. ⇒ ⭐ *Il metro è stato corretto dalla sua stessa
taratura, prima di misurare qualsiasi cosa.*

### 5.9 ⭐⭐⭐⭐⭐ E QUEL CHE SI VEDE — **il desktop remoto è perfetto, e Firefox si ferma su un dialogo**

#### ⭐⭐ Il desktop: ![il desktop remoto con Nautilus aperto](scatti/10-desktop-remoto-nautilus.png)

⭐ **GNOME completo, sfondo Debian, barra in alto, e Nautilus con una finestra vera, nitida** —
`[M]` media da **75,2 a 114,0** quando la finestra si apre. ⇒ ⛔ **compositore, GTK, `wl_output`,
mappatura, cattura, codifica, filo: tutta la catena regge.** Il prodotto fa quel che promette.

#### ⛔ E Firefox: ![Firefox fermo sul dialogo «Profile Missing»](scatti/10-firefox-profile-missing.png)

> **Profile Missing** — *«Your Firefox profile cannot be loaded. It may be missing or
> inaccessible.»* **[OK]**

`[M]` Riprodotto **tre volte**, anche con `~/.mozilla` **spazzato via** e ripartendo da zero.
Premendo OK, Firefox **esce**. ⛔ **`profiles.ini` non viene mai creato**: in `~/.mozilla/firefox/`
restano solo `Crash Reports` e `Pending Pings`. E il primo crash è **datato e nominato**:
`MozCrashReason: "Compositor crashed ()"`, **`SIGSEGV / SEGV_MAPERR`**.

> ### ⛔⛔ E LA TRAPPOLA CHE TENEVA NASCOSTO TUTTO ERA DEL BANCO
>
> L'**ESC** che si manda per uscire dalla vista d'insieme di GNOME è ⛔ **lo stesso tasto che chiude
> un dialogo modale**. Con ESC prima dello scatto → **desktop vuoto**. Senza ESC → **il dialogo**.
>
> ⇒ ⭐⭐ *«Firefox è vivo e disegna ma non ha nessuna finestra»* — la diagnosi su cui il
> coordinamento aveva girato per ore — **era il dialogo, chiuso dal nostro stesso ESC.**

⚠ **E una seconda causa reale, trovata per strada, che riguarda i banchi**: l'ambiente composto da
`giu()` (`env -i` con otto variabili) ⛔ **manca `XDG_SESSION_TYPE`** — Nautilus rifiutava con
*«Unsupported or missing session type ''»*. Servono anche `XDG_CURRENT_DESKTOP=GNOME` e
`GTK_A11Y=none`.

⛔ **Che cosa resta `[?]`**: **perché** Firefox non riesce a creare il profilo. `HOME` è scrivibile,
ci sono **28 GB** liberi, il portale è attivo, e `gdb` mostra un ciclo `g_main_context_iteration`
**annidato** — cioè il dialogo. ⭐ La pista che pesa è il **compositore di Firefox che muore**: se il
processo GPU se ne va all'avvio, *«Profile Missing»* è **il sintomo, non la causa**.

### 5.10 ⭐⭐⭐⭐⭐ **«FIREFOX NON FUNZIONA» — ed era il profilo del browser che non nasceva**

*25 agosto 2026.* ⛔ **Il difetto è di REMOTIX** — ed è per questo che sta in questa fase e non
altrove.

> #### ⭐⭐⭐ CORREZIONE DELL'UTENTE — *25 agosto 2026, sera*
>
> ⚠ *Questa sezione si intitolava «**ed era `~/.cache` che punta a `/tmp`**» e diceva «**il difetto
> non era di REMOTIX**». ⛔ Tutt'e due sbagliate, e la seconda nel verso peggiore.*
>
> > *«`.cache` che punta a `/tmp` è una mia scelta voluta»* — l'utente. È una decisione su come deve
> > funzionare **il sistema operativo della sua macchina**, e **non c'entra niente con REMOTIX**.
>
> ⇒ ⛔ **Quel collegamento non è un difetto, e non c'è niente da riparare nel sistema.** Su una
> macchina a un utente solo non fa nessun danno.
> ⭐⭐ **Il difetto è nostro**: è **il nostro `useradd -m`** a creare dieci utenti che nascono tutti a
> scrivere nello stesso posto. ⇒ *Una scelta innocua diventa un blocco per nove **perché ci mettiamo
> noi i dieci inquilini**.*
> ⇒ `DECISIONI.md` **§4.6-undecies**, e il bersaglio della fase 11 cambia di conseguenza:
> **«il secondo utente apre il browser?»**, non «le cartelle sono al posto canonico?».

#### Il meccanismo, nudo — **senza browser, senza compositore, senza GPU**

```
$ mkdir -p ~/.cache/mozilla                    # da «provanic3»
mkdir: cannot create directory '/home/provanic3/.cache/mozilla': Permission denied

$ ls -ld /etc/skel/.cache
lrwxrwxrwx  root root   /etc/skel/.cache -> /tmp          ← immagine base, 30 luglio
$ ls -ld /tmp/mozilla
drwx------  prova2 prova2  /tmp/mozilla                   ← creata il 23 agosto 08:03
```

⇒ `/etc/skel/.cache` è un **collegamento a `/tmp`** — ⭐ **per scelta dell'utente**, vedi il riquadro
in testa alla sezione — e `src/provisiona.sh` · `useradd -m` crea gli utenti con `useradd -m`, che **copia lo
scheletro** ⇒ ⛔ **ogni utente che facciamo noi eredita `~/.cache -> /tmp`**. Firefox tiene il
profilo *locale* sotto `$HOME/.cache/mozilla`, cioè sotto **`/tmp/mozilla`**.

⛔⛔ **Il PRIMO utente che apre il browser crea `/tmp/mozilla` a nome suo e a modo `0700`.** Da quel
momento nessun altro ci può scrivere, `profiles.ini` **non nasce mai**, e il browser apre una
finestra che dice *«Your Firefox profile cannot be loaded»*.

> ### ⭐⭐⭐ E QUESTO È ESATTAMENTE IL TEMA DELLA FASE
>
> ⛔ **È un difetto che su una macchina a UN utente non si vede mai, e che su dieci ne blocca nove.**
> Il multi-tenant non lo ha creato: **lo ha reso certo**. ⇒ *Un prodotto che passa da un inquilino a
> dieci non eredita solo i suoi difetti: ne sveglia di dormienti.*

#### ⭐ E il colpevole ha un nome e una data — **ed è il caso del regista**

`[M]` `/tmp/mozilla` appartiene a **`prova2`**, creata il **23 agosto alle 08:03**. E **`prova`** —
⭐ **l'utente con cui il regista entra** — aveva `~/.cache -> /tmp`.
⇒ ⛔ **Ecco perché per lui non funzionava.** Non un caso, non una configurazione strana: **il turno**.

#### Il rosso, il verde e il controllo negativo

| | `[M]` |
|---|---|
| **ROSSO** — `~/.cache -> /tmp` | finestra vera che dice **«Profile Missing»**; `profiles.ini` **non nasce mai** |
| ⭐ **VERDE** — `~/.cache` cartella vera | ![Firefox curato, con tre schede e una pagina resa](scatti/10-firefox-curato.png) barra, **tre schede**, campo indirizzo, **pagina resa** |
| ⛔ **CONTROLLO NEGATIVO** — rimesso il collegamento | **torna rosso**: 30 s, nessun `profiles.ini` |
| ⭐ **e su un secondo utente** (`provanic3`, `.mozilla` spazzata, **sotto lucchetto**) | verde uguale ⇒ **regge nel multi-tenant** |

#### ⛔ La pista del compositore è REFUTATA, e con tre prove

⚠ Sembrava buona: `MozCrashReason: "Compositor crashed ()"`, `SIGSEGV / SEGV_MAPERR`. ⛔ **E non
era la causa:**

1. il guasto si riproduce **headless, senza compositore, senza sessione, senza REMOTIX**;
2. con la cura Firefox rende una pagina **coi predefiniti** — nessun `MOZ_DISABLE_GPU_PROCESS`,
   nessun `LIBGL_ALWAYS_SOFTWARE`;
3. nel profilo curato **zero dump di crash**.

⇒ ⭐ *Un crash che c'è davvero non è per questo la causa di quel che si sta guardando* — è
`LEZIONI.md` §1.35 dall'altro capo.

#### La cura, e **dove** sta

⭐ In **`src/provisiona.sh`** — cioè **nella macchina, non nel prodotto** (`SPECIFICHE.md` §5.9,
parte A): **agli utenti che creiamo noi** una `~/.cache` **vera** se è un collegamento o manca.
⚠ **Non si tocca `/tmp/mozilla` di chi ce l'ha già**: non è nostro e non si sa chi lo usa.
⭐⭐ **E non si tocca né `/etc/skel` né la home dell'utente**: la sua scelta resta in piedi, e la cura
vale **solo per i nostri inquilini**. ⇒ *È il modo giusto anche a correzione avvenuta.*

⛔ **E il predicato di verifica non guarda il collegamento: PROVA A SCRIVERE** — perché *«scritto non
è in vigore»* (**E1**). `[M]` collegamento ⇒ rosso · cartella non scrivibile ⇒ rosso · curato ⇒
verde, **4 su 4**.

⚠ **E va rilanciato dopo ogni riavvio**: il rootfs della macchina di prova sta **in RAM**.

### 5.11 ⚠ E UNA COSA CHE NESSUNO SI ASPETTAVA: **il desktop nasce dentro la PANORAMICA**

![quel che si vede appena entrati: la panoramica delle Attività](scatti/10-appena-entrato-panoramica.png)

⭐ **Questo è quel che l'utente vede nell'istante in cui entra**, guardato col testimone su una
sessione appena nata: ⛔ **non un desktop, ma la panoramica delle Attività** — *«Type to search»*, il
molo con Firefox e File, e lo spazio di lavoro in anteprima.

⚠ È il comportamento **normale** di GNOME su una sessione senza finestre, e ⭐ **una strada usabile
c'è** — si preme `Esc`, oppure si clicca un'icona nel molo. ⛔ **Ma per chi guarda, *«una finestra che
non riesco a raggiungere»* e *«non funziona»* hanno la stessa faccia** — e in tutta la documentazione
del progetto la parola **panoramica** non compare mai.

⛔ **E qui la panoramica ha morso davvero due volte:**

1. il coordinamento premeva `Esc` per uscirne prima di scattare — ⛔ **e `Esc` è lo stesso tasto che
   chiude un dialogo modale.** ⇒ *«Firefox è vivo e disegna ma non ha nessuna finestra»* **era il
   dialogo, chiuso dal nostro stesso `Esc`**;
2. ⚠ e il regista, che di `Esc` non sapeva niente, ha visto **la panoramica** e un browser che non
   parte.

⇒ `[?]` **Se la sessione debba nascere sul desktop invece che nella panoramica è una decisione sua**,
perché cambia **quel che l'utente vede** (**I6**, **I8**). ⛔ E la cura, qualunque sia, non può essere
un trucco che vale **solo per GNOME**: le fasi 11 e 12 portano KDE, XFCE e LXQt
(`DECISIONI.md` §4.6-sexies).

### 5.12 ⭐⭐⭐ I SEI DIFETTI RIMASTI — **sei curati, zero rimandati**

*25 agosto 2026, la coda della fase.* ⭐ `banchi/10-f3-cure.py`, **`--certifica` 42 su 42**.

| # | il difetto | ⭐ il rosso e il verde |
|---|---|---|
| **1** | ⛔⛔ **le righe nuove erano MUTE**, ⛔ **la riga dello SFRATTO compresa** — quella che dice **chi** è stato buttato fuori | `wt_chi()` e **87 punti di stampa** passati a `registro_dice_di()`. `[M]` area `wt`: **0,0 % → 79,2 %** e **0,0 % → 77,3 %** su due scene; col classificatore certificato di `10-b96` (31/31) le righe di diagnosi vanno da **98,8 % a 100 %**. ⭐ **Non previsto**: ha alzato anche l'area `rcp` da **35,6 % a 89,8 %** — molte righe `REG_RCP` le scrive `webtransport.c`, non `rcp.c` |
| **2** | ⛔⛔ **`fermo_ms=` MENTIVA**: il commento diceva «per sessione», il codice leggeva un contatore **globale** | `[M]` `SIGSTOP` di **6,0 s** al ciclo del padre con **nessuna sessione viva**, poi si apre la sessione: **`fermo_ms=6143` → `0`**. ⭐ **E il controllo negativo**: sessione **viva durante** lo stallo, **5800 → 5647** ⇒ *il testimone è stato **corretto**, non spento* |
| **3** | ⚠ due **commenti bugiardi**, e la **quinta copia a mano** del tetto | curati. ⛔ **E `WT_RIPASSO_INSIEME 32` NON si unifica** — vedi il riquadro |
| **4** | ⚠ il **`pkill` globale** in due banchi | ristretto a quel che il banco ha acceso lui. ⛔ In `10-b97` erano sbagliati **tutt'e due nel verso peggiore**: uno aveva la cartella di **un altro banco scritta a mano** — uccideva i clienti del vicino e lasciava vivi i propri |
| **5** | ⚠ il **`sed` che ricompilava** il tetto in tre terreni | tolto. ⛔ **E il rosso è che oggi non morde più**: il modello combacia con **0 righe** ⇒ `10-b2`, `10-b93` e `10-c3` **non partivano affatto**. ⭐ La guardia **cambia posto**: si legge il tetto **dal server acceso**, non dal testo da cui nascerà |
| **6** | ⚠ l'**ambiente incompleto** dei banchi (`XDG_SESSION_TYPE` e altre due) | curato, e ⭐ **le copie erano quattro, non tre**: adesso in un posto solo, `banchi/10-ambiente-sessione.sh` |

> ### ⛔ PERCHÉ LA QUINTA COPIA **NON** SI UNIFICA — e la ragione è scritta accanto al codice
>
> ⭐ `WT_RIPASSO_INSIEME 32` **non è la stessa quantità** di `RCP_TETTO_SESSIONI`, per due motivi
> indipendenti:
>
> 1. è la misura di **un lotto**, non di una **capienza**: chi non ci sta **entra nel giro dopo**, e
>    la proprietà difesa è *«un numero **fisso** di chiamate invece di `N`»* — non *«una»*;
> 2. ⛔ dev'essere una **costante di compilazione**: dimensiona **quattro array sullo stack**
>    (`quali[32][160]` = 5 KiB) mentre il tetto ormai **si muove a caldo**. ⇒ Legarli darebbe un
>    **VLA scelto dalla riga di comando dentro il ciclo che consegna i fotogrammi**.
>
> ⚠ **Ma il commento mentiva davvero** — diceva *«32 sta sopra i **sedici** posti»*, un letterale e
> per giunta invecchiato. ⭐ Sostituito col legame vero, **una disuguaglianza in un verso solo**,
> messa dove **il compilatore la fa valere**: `_Static_assert(WT_RIPASSO_INSIEME >= RCP_TETTO_SESSIONI)`.
>
> ⇒ ⭐⭐ *Unificare per simmetria quel che non è la stessa quantità è un difetto nuovo, non una cura.*
> È la stessa ragione per cui `MAX_IN_VOLO` era già stato lasciato fuori.

> ### ⛔⭐ E LA SCOPERTA CHE VALE PIÙ DELLA CURA: **il metro che i banchi usavano è CIECO**
>
> `[M]` Il conto dei processi vivi — *«si **conta** chi è vivo»*, in `10-b89-scena.sh` e
> `10-b92-dieci.py` — ha detto **1 in tutt'e tre i casi**: ambiente rotto, ambiente curato, ambiente
> rotto di nuovo.
>
> ⇒ ⛔⛔ **Il processo SOPRAVVIVE al proprio fallimento.** Quel metro direbbe *«due finestre vive»* su
> un desktop **senza nessuna finestra** — ed è esattamente il buco in cui il coordinamento era
> caduto per ore (§5.9). ⭐ Il predicato nuovo giudica **la riga che il programma scrive**, non il
> processo, e tiene il conto accanto **come testimone di sé stesso**.

### 5.13 ⭐⭐⭐⭐⭐ **IL PRODOTTO CUCITO GIRA — e Firefox apre una finestra vera**

![Firefox nel desktop remoto, sul prodotto finale della fase](scatti/10-firefox-nel-prodotto-cucito.png)

⭐ **Albero cucito, compilato pulito** (le gemelle R12.3 allineate, il controllo positivo del
costruttore verde), acceso sulla **8400** con `--budget-mpixel-s 480 --riserva 0.5
--tetto-sessioni 10`. `[M]` Le righe d'avvio dichiarano i tre valori in vigore, e ⭐ la riga del
guardiano porta il **denominatore** che prima non c'era: `inquilini=0`.

⇒ ⭐⭐⭐ **E questo è il desktop remoto del prodotto finale**, guardato col testimone: **Firefox con
due schede, la barra degli indirizzi, e una pagina resa**. ⛔ **Nessun dialogo, nessun profilo
mancante, nessun accorgimento**: l'ambiente giusto e una `~/.cache` che è sua.

### 7.4 ✅⭐⭐⭐ **LA SESSIONE CHE NASCE CIECA — CHIUSA il 27 agosto 2026: erano i GRUPPI dell'inquilino**

> ## ⭐⭐⭐ LA RISPOSTA, prima del racconto
>
> `[M]` **L'inquilino non era nei gruppi `video` e `render`.** Tutto qui.
>
> | | |
> |---|---|
> | inquilini **con** i due gruppi | `[M]` **17 sessioni su 17** vedono: 9 nuove e mai usate in **1,92–2,10 s**, 8 riattacchi in **1,03 s** |
> | inquilini **senza** (creati come li creava `terreno10.sh`) | `[M]` **0 su 4** — mai in 90 s, zero fotogrammi, e la sessione gira in tondo fra *«ZERO MONITOR»* e *«monitor virtuale montato»* per **82 s** |
> | ⭐ **la controprova** | dati i due gruppi **allo stesso inquilino** e fatto rinascere il gestore d'utente ⇒ **2,04 s**, 14 fotogrammi. ⭐⭐ **Una variabile sola, esito ribaltato** |
>
> ⭐⭐ **E la tabella qui sotto si spiega da sola**: `provanic4/5/6` — quelli che non videro **mai**, su
> **98 · 55 · 50** tentativi — oggi **non hanno** né `video` né `render`. `prova` e `provanic1`, che
> videro **sempre**, **li hanno**. ⇒ ⛔ Non era intermittente: erano **due popolazioni di inquilini**.
>
> ⚠ **E quel che ha reso il difetto così caro non è il difetto: è che non diceva niente.** Un
> inquilino senza quei gruppi non produce nessun errore — produce una sessione che *sembra* nata e
> non si vede. ⇒ La cura è in due pezzi:
> · `src/provisiona.sh` legge adesso il gruppo **dal nodo** (`stat -c %g` sui `cardN`/`renderDN`),
>   ⛔ non da un nome inchiodato — e la verifica confronta i **gid**, non la parola «render»;
> · ⭐⭐ `src/figlio.c` controlla alla nascita di **ogni** sessione e, se il gruppo manca, scrive nel
>   registro *«NON È NEL GRUPPO DELLA SCHEDA … QUESTA SESSIONE NASCERÀ E NON VEDRÀ NIENTE»* **con la
>   cura completa dentro la riga**. ⛔ Dichiara, non rifiuta.
>
> ⛔ **E c'è una coda che tocca le misure del passato**: i **banchi** creavano inquilini per conto
> loro — `banchi/attrezzi-utenti.sh` e nove terreni delle fasi 02, 04, 06, 07, 09 — ⛔ **senza quei
> gruppi**. ⇒ Ogni banco che ha misurato su un inquilino così ha misurato **una sessione che non
> vedeva, senza saperlo**.
>
> ⚠ **Due rilievi misurati che valgono per chiunque legga questo registro:**
> · ⛔ **`ZERO MONITOR` è TRANSITORIO su ogni sessione sana** — `[M]` compare **173 ms** prima che il
>   monitor esista. Chi lo legge come prova di cecità dà **falso rosso su tutte**;
> · ⚠ al **riattacco** `formato negoziato` **non si ripete** se il formato non cambia. Non è cecità.
>
> ⛔ **E il «terzo stato» di questa sezione — la riga `(0 prima, 2 dopo)` — non esiste**: era
> **memoria non inizializzata** (`src/figlio.c` · `codifica_e_manda()` spediva la struttura prima del `memset` di
> `:5311`). ⇒ `LEZIONI.md` §1.55. Curato.
>
> ⇒ Il racconto che segue resta **come fu scritto**, perché è la storia di una caccia e le quattro
> ipotesi refutate valgono ancora. ⛔ Ma il difetto **è chiuso**, e la fase 11 §7-bis.19 ha i numeri.

#### Il racconto originale, com'era scritto

*Trovato il **25 agosto 2026, sera**, dalla prova che ha proposto il regista: «dieci subagenti che
usano il desktop in modi diversi».* ⭐ **Il difetto è emerso PRIMA che la prova partisse**, perché la
prova costringeva ad aprire **sessioni nuove** — ⛔ e nessuno l'aveva mai fatto.

⛔⛔ **Su una sessione appena nata, Mutter non annuncia nessun `wl_output`.** ⇒ **Nessuna applicazione
Wayland può aprire una finestra:**

| | `[M]` |
|---|---|
| **Firefox** | resta vivo — **un processo solo**, mai quello di contenuto — e sputa **in continuo** `gdk_monitor_get_workarea: assertion 'GDK_IS_MONITOR (monitor)' failed` |
| **mpv** | esce: *«No outputs found or compositor doesn't support wl_output (ver. 2)»*, **4 uscite video su 4** |
| il compositore | ⭐ **0,0 %** del motore di disegno · il palco consegna **zero fotogrammi** |

#### ⭐ Il prodotto SE NE ACCORGE e lo dichiara — non consegna nero in silenzio

```
sessione [provanic9] ⛔ ZERO MONITOR, e la sessione e' viva: e' la sessione
                        «viva, completa e NERA» di STUDI.md §gnome §3.1
figlio   il palco di «provanic9»: monitor «» (0 prima, 0 dopo), 0x0 stride 0 a 0 bit
```

#### ⛔ Che cosa NON è — quattro ipotesi refutate, una per una

| ipotesi | ⛔ refutata da |
|---|---|
| *«è una corsa persa all'avvio»* | a **+73 s** mpv ancora non trova l'uscita (provato a +5, +11, +23, +43, +73) |
| *«il cliente non dichiara la vista»* | `--adatta 1920x1080@1.0` **non cambia niente**: `provanic7` (senza) e `provanic8` (con) **identici** |
| *«è il multi-tenant»* | con **tutte le sessioni chiuse**, una sessione **da sola** ha lo stesso `wl_output = 0` |
| *«è degli utenti nuovi»* | ⭐⭐ **`provanic3` ha avuto il monitor 2 volte e poi 6 volte NO** — lo stesso utente |

⇒ ⛔ **È intermittente**, e da un certo momento in poi non riesce più:

| utente | riuscito | fallito |
|---|---|---|
| `prova`, `provanic1` | 1 | 0 |
| ⭐ `provanic3` | **2** | ⛔ **6** |
| `provanic4` · `provanic5` · `provanic6` | 0 | ⛔ **98** · **55** · **50** |

⚠ E c'è un **terzo stato**: `monitor «» (0 prima, **2** dopo)` — una volta per utente ne nascono
**due**, senza nome.

#### ⭐ La pista che pesa, e sta nel nostro codice

`src/sessione.c` · la nota «`--virtual-monitor` non c'e' piu'», e il commento è del **14 agosto 2026**:

> ⛔⛔ *E `--virtual-monitor` NON C'È PIÙ.* Fino a stamattina questa riga lo chiedeva, e **la sessione
> nasceva con un monitor suo**. ⇒ Poi… *«il nostro `RecordVirtual` ne crea uno»*.

⇒ Da allora il monitor **non lo chiediamo più**: si conta che lo crei `RecordVirtual`. ⛔ **E adesso
non lo crea, o lo crea solo a volte.**

⚠ **E c'è una guardia che rifiuta di rimetterlo** (`sessione.c` · `scrivi_dropin()`). ⇒ ⛔ *Chi curerà deve leggere le
righe 740-840 per intero: è stato tolto per una ragione misurata, e rimetterlo alla cieca rifà il
difetto che quella riga aveva curato.*

#### ⛔⛔ E L'ERRORE DI METODO CHE L'HA NASCOSTO — **è il più grave della fase**

⛔ **Nessuno ha mai aperto una sessione NUOVA e l'ha guardata.** Tutte le prove — quelle della fase
comprese — hanno riusato sessioni **già aperte, che il monitor ce l'avevano**.

⇒ ⭐⭐ **È `LEZIONI.md` §1.37 un piano più giù**: là il difetto era *«non si sapeva guardare»*; qui è
*«si guardava sempre lo stesso pezzo di scena»*. ⚠ E il conto dei processi diceva **1** in tutt'e due
i casi — ⛔ **finestra o non finestra, lo stesso numero.**

⚠ **Che cosa NON tocca**: i numeri di capacità di §6 e §10 sono presi su sessioni che **disegnavano
davvero** — fotogrammi contati e GPU letta. ⇒ ⭐ **Il «da sei a undici» resta valido.**
⛔ **Che cosa tocca**: la consegna. *Oggi una sessione nuova su tre-quattro nasce cieca*, e chi la
prende non vede aprirsi nessuna finestra.

### 7.5 ⛔⛔ **FERMARE IL SERVER PORTA VIA TUTTE LE SESSIONI** — anche per aggiornarlo

*Trovato il **25 agosto 2026 alle 18:14**, aggiornando la 7730 su richiesta del regista.*

`[M]` **La sequenza, dal giornale di sistema:**

```
18:14:29  Stopping remotix-7730.service …   Deactivated successfully.   Started …
18:14:44  New session c686 of user prova    ← una sessione NUOVA E VUOTA
```

⇒ ⛔ **La sessione dell'utente è morta con l'unità**, con dentro il terminale e il browser che aveva
aperto. Il palco vive **nell'albero di processi del server**, e l'unità ha `KillMode=mixed`.

⭐ **`SPECIFICHE.md` §5.2 dice «la sessione sopravvive al CLIENT», ed è vero e misurato.**
⛔ *«Sopravvive al server»* **non era mai stato promesso, e non è vero.**

⇒ ⛔⛔ **Oggi aggiornare il server vuol dire buttare fuori tutti** — lo stesso danno che
`DECISIONI.md` §4.7 vieta a chiunque di provocare spegnendo la macchina, ⚠ **fatto però da chi
amministra, e senza che nessuno l'avesse dichiarato.**

⚠ **Il confine è ora scritto** in `SPECIFICHE.md` §5.2, e il posto dove si cura è la **fase 14, il
servizio**: aggiornare senza fermare nessuno.

⭐ **E per intanto la regola pratica**: prima di riavviare il server **si guarda chi c'è**, come §4.7
già impone a chi vorrebbe spegnere la macchina.

⚠ **E oggi non costa niente, e va detto**: *«nessuno sta lavorando sul server, REMOTIX è
ancora in sviluppo»* — l'utente, 25 agosto 2026. ⇒ ⭐ **Il rilievo non è un'emergenza: è un
confine scritto adesso perché il giorno in cui ci sarà qualcuno dentro, si sappia già.**

---

## §8 · Le decisioni prodotte

> ⛔ *Scritto dopo i due giri di misure, quando il prodotto non era ancora stato toccato: «nessuna di
> queste è presa… `src/` è intatto, nessun commit».*
>
> ### ⭐⭐ E POI IL REGISTA HA DATO L'ORDINE — *24 agosto 2026*
>
> > *«Prima applica le patch, poi scrivi il prodotto e dopo rifai i test.»*
>
> ⇒ ⭐ **Le decisioni di §8.1 sono state prese e SCRITTE nel prodotto**, e i difetti di §8.2 curati o
> rinviati con la ragione. **Quel che è stato fatto sta in §5**; qui sotto restano le decisioni
> **come sono maturate**, perché è da lì che vengono, ⭐ **con lo stato di ciascuna in fondo alla
> riga**.
>
> ⚠ **E due sono ancora del regista, e solo sue**: sono in fondo a §8.2.

### 8.1 ⭐ Le decisioni di disegno — che cosa diventa il budget

| # | la decisione | il numero che adesso c'è |
|---|---|---|
| **D1** | ⛔⛔ **Il budget non è di codifica: è di COMPOSIZIONE.** `DECISIONI.md` §4.6 va **corretta**, non integrata | `[M]` soffitto della composizione **0,97 Gpixel/s** contro **1,86** (H.264) e **2,33** (HEVC) del codificatore — §6.11, §6.2, §6.10. E `[M]` a saturare `rcs0` è **`gnome-shell` al 99,5 %**, mentre `remotix` sta a **0,00 %** (§6.15) |
| **D2** | ⭐⭐ **Il tetto è un conto di LAVORO, non di sessioni** | `[M]` dieci inquilini **fermi** accanto a uno che lavora costano **+0,2 %** (§6.16); l'**ottavo saturo** porta tutti a **1,5 fot/s** (§6.5). ⇒ ⛔ Un tetto che conta le teste **sbaglia in tutt'e due i versi** |
| **D3** | ⭐⭐⭐ **Il budget si può calcolare PRIMA**, e la moneta è il **pixel** | `[M]` ai cedimenti i Mpixel/s coincidono entro lo **0,6 %** fra 1080p e 4K, mentre i fot/s differiscono del **74,9 %** (§6.9). ⛔ **Ma prima dei pixel si guarda il RITARDO**, o il conto dice *«c'è posto»* mentre tutti stanno a 1,5 fot/s |
| **D4** | ⭐ **La regola proposta è «riserva 50 %»**, con la manopola in mano al regista | `[M]` 0 falsi sì, 0 falsi no, tetto **6 sature / 10 ferme** — ⭐ **il dieci di `SPECIFICHE.md` §5.5 ritrovato per misura invece che per promessa** (§6.9) |
| **D5** | ⭐ **`BUDGET_PIENO 0x06` si AGGIUNGE a `0x0E`**, non lo sostituisce: due limiti diversi, **due gesti diversi** per l'utente | §6.4 · e ⛔ `0x0E` **è stato visto scattare per la prima volta**, 10 su 10 |
| **D6** | ⛔ **Il no va detto PRIMA di far nascere il figlio**, in `consegna_verdetto()` | `[M]` un utente **mai ammesso** aveva **42 processi e un `gnome-shell`** (§6.4) |
| **D7** | **I quattro `#define` a 16 diventano uno**, più il tetto configurabile — ⛔ e `WT_PALCHI 8` va con loro, perché **morde a nove** | §3.3, §4.2 |
| **D8** | ⚠ **`--budget-mpixel-s` NON si auto-tara**: prima che la macchina abbia ceduto una volta, la capacità è **un limite inferiore, non un soffitto** | §6.9 |

### 8.2 ⛔ I difetti di prodotto che aspettano una decisione — **e cinque su sette non c'entrano col multi-tenant**

| # | il difetto | quanto è grosso |
|---|---|---|
| **P1** | ⛔⛔⛔ **Il figlio muore di SIGSEGV su una larghezza di finestra qualsiasi**: passo del DMA-BUF non multiplo di 64 ⇒ *«rimonto sulla memoria»* e **2 ms dopo è morto**. `[M]` **3 su 3** a 1268 (quella che Firefox apre di suo), **0 su 3** a 1280 | ⛔⛔ **rompe il prodotto per un utente solo.** ⭐ Ed è lo stesso codice che rifiuta la **tela minima** dichiarata in §5.5 (§6.8, §6.2) |
| **P2** | ⛔⛔⛔ **Regolatore + linea morta formano un ANELLO CHIUSO che sfratta chi lavora**: `[M]` cinque client sfrattati in **1,3 s** a cinque sessioni. ⭐ **Spegnendo l'una O l'altra, 8 su 8 sopravvivono** | ⛔⛔ viola *«mai staccare»*, ed è **provato da due strade** (§6.15) |
| **P3** | ⛔⛔ **L'undicesimo è AMMESSO e non vede un pixel**, e sul filo **non esce niente** | ⛔ i due `16` si liberano su **eventi diversi** (§4.1) |
| **P4** | ⛔⛔ **Il guardiano di logind è sincrono nel ciclo che consegna**: `[M]` la frontiera si restringe **come 1/N** e taglia **i 300 ms che il codice si concede** a ~4 inquilini. A N=7 con D=286 ms **ogni desktop crolla a 1,3 fot/s e non si scrive una riga** | ⛔ degrado **silenzioso**; ⚠ **lo sfratto NON è l'esito ordinario** — il rilievo va corretto lì (§6.13) |
| **P5** | ⛔ **La linea morta stacca su un buco di 10 s fra due scene**, non solo su un desktop fermo — `[M]` su una sessione che un attimo prima faceva 60 commit/s | ⛔ e `[M]` **un `SIGSTOP` di 5 s a un figlio uccide TUTTE le sessioni**: un figlio fermo lascia byte fermi **nella coda del padre** (§6.11, §6.7) |
| **P6** | ⚠ **Il registro non dice di chi è**: `[M]` solo il **4,2 %** delle righe di diagnosi è attribuibile, e la prova cieca dà **0 nomi su 4** | ⭐ **la cura è di tre righe** e costa **+7,8 %** di byte, e la diagnosi cieca torna il nome giusto (§6.7) |
| **P7** | ⛔ **QVBR — la cura di banda della fase 9 — esiste, funziona, e nessuno la accende**: il predefinito è a qualità fissa, e il tetto **non è fra le cinque cure** | ⭐ `[M]` obbedisce entro il 5 %, e la manopola copre **8,8×** di banda (§6.10) |

> ### ✅⏳ **IL BAN PER INDIRIZZO È DECISO: si RINVIA, con un nome** — *25 agosto 2026*
>
> *«Il discorso del ban rientrerà in un discorso più generale sulla sicurezza, che farà parte di un
> capitolo evolutivo»* — l'utente. ⇒ **`DECISIONI.md` §4.6-octies**.
>
> ⛔ **Il rilievo R10-A2 resta vero e non si chiude: si rinvia.** ⭐ Ed è la scelta giusta, perché la
> cura **tocca una difesa, non una comodità**: non si smonta dentro una fase che sta misurando la
> capacità.
> ⚠ **Il prezzo, dichiarato**: fino a quel capitolo, **un ufficio dietro un NAT è una configurazione
> in cui il prodotto può chiudersi da solo per dodici ore** — ⭐ e non è un difetto nascosto, è un
> difetto **misurato, nominato e datato**.

> ### ⛔⛔ E QUESTE DUE SONO DEL REGISTA, E SOLO SUE
>
> ⭐ *Nessuno le può prendere al posto suo, perché tutt'e due cambiano **quel che l'utente vede**, ed
> è l'invariante **I8**: il metro è quel che l'utente vede.*
>
> | | la domanda | quel che la misura ha già messo sul tavolo |
> |---|---|---|
> | **QVBR** — cioè **P7** | ⭐ **si accende il tetto di banda della fase 9, oppure no?** | `[M]` La cura **esiste, funziona e obbedisce entro il 5 %**, e la manopola copre **8,8×** di banda. ⛔ **Ma oggi è spenta**, e il predefinito è a **qualità fissa**. ⚠ E il caso in cui v1 si fece male — QVBR **con un desktop vero dietro** — è ancora `[?]` (§9): il banco c'è, manca il giro |
> | **i numeri di fabbrica** | ⭐ **tetto 10 e riserva 0,5 restano così?** | `[M]` Con riserva **0,5**: **0 falsi sì, 0 falsi no**, e il tetto ritrovato è **6 sature / 10 ferme** — ⭐ cioè **il dieci di `SPECIFICHE.md` §5.5 riconquistato per MISURA invece che per promessa**. ⚠ Ma sono i numeri di **questo ferro**: un'altra macchina vuole un altro `--budget-mpixel-s` |
>
> ⛔ **E il budget nasce SPENTO** (`--budget-mpixel-s 0`) per l'invariante **I6**: quel che cambia
> ciò che l'utente vede **non si accende da solo**. ⇒ ⭐ **Accenderlo è la prima delle due
> decisioni.**

---

## §9 · Che cosa resta `[?]`

| `[?]` | come si chiude |
|---|---|
| ⛔ **Il soffitto del DESKTOP VERO**: `[M]` a undici sessioni si sta al **22-24 %** della GPU, e **sono finiti gli utenti, non la macchina** | più utenti, o tele più grandi. ⚠ L'estrapolazione direbbe ~46 ed è **quattro volte fuori dal misurato**: non si riferisce |
| ⛔ **Il dirupo sulla scena vera**: dentro undici **non esiste**; a che numero ci sia, non si sa | la stessa salita, più in là |
| ⛔ **Perché la transizione è NETTA** invece che proporzionale dentro `i915`/mutter | c'è il correlato (pixel composti) e il punto d'attesa (`ioctl` DRM), **non la regola dello scheduler** |
| ⛔ **La verifica in avanti ALLA CIECA del predittore**: le quattro previsioni restano **sigillate** con l'impronta | `bash banchi/10-b99-lancia.sh avanti` + `confronta`, da chiunque vinca un turno |
| ⛔ **Chrome**: `DECISIONI.md` §7.20 dichiara due motori, ne è girato **uno** | rifare §6.8 sull'altro |
| ⛔ **QVBR con un desktop VERO dietro** — ⚠ *ed è proprio la scena su cui la fase 10 di v1 fu azzerata* | il banco c'è, manca il giro |
| ⛔ **La rete VERA**: i clienti girano sulla stessa macchina, su `lo` ⇒ il filo è **contato, non provato** | `wondershaper` sul percorso vero |
| ⚠ **Il numero di §6.3 sulla scena dura**, che §6.14 misura **due volte più grande** | rifare quella cella col metro di §6.14 |
| `[?]` **Un danno che sopravvive alla sua causa**: due sessioni restano a 7-9 fot/s **col guardiano a zero e le scene che disegnano** | meccanismo ignoto, riferito come **osservazione** |
| ⛔ **Perché Firefox non crea il profilo NEMMENO da solo**, cioè il crash `Compositor crashed ()` che resta nel registro anche col profilo curato | ⚠ È **un secondo difetto**, dichiarato e lasciato stare: la cura di §5.10 fa partire il browser, e questo non morde più |
| ⛔ **«Si può cliccare e scrivere dentro»** | ⚠ `[M]` provato come *«si apre, disegna, rende una pagina»* — **non** come *«ci clicco dentro»*: il cliente di prova manda **solo `PUNTATORE`**, non ha bottoni né tasti (§7.3). ⇒ Va esteso il cliente |
| ⚠ **La sessione nasce nella PANORAMICA** invece che sul desktop (§5.11) | ⛔ **è una decisione del regista**, non un `[?]` da misurare: cambia quel che l'utente vede |
| ⚠ **Undici `segfault` di `remotix` in `libei.so.1.3.901`** (`segfault at 50`, cioè NULL+0x50) — ⭐ **ma sono tutti PRIMA della cura** | ⭐ `[M]` **L'ultimo è delle 07:06 del 25 agosto**; la cura di `src/input.c` (§5, `stacca_il_contesto()`) è stata cucita **alle 14:47**, e da allora **nessuno** — attraverso un pomeriggio di tre incarichi, decine di sessioni aperte e chiuse. ⚠ **È un indizio forte, non una prova controllata**: il rosso non è stato riprodotto di proposito sull'albero curato |
| ⛔⛔ **L'IMMAGINE** | ⭐ **Il testimone adesso c'è** (§5.8) e il desktop remoto **si è visto**: è perfetto. ⚠ Ma *«si vede peggio»* nessun banco lo dice — quello lo dice il regista, ed è §10 |

---

## §10 · Il giudizio dell'utente

### ⭐⭐⭐⭐⭐ 25 agosto 2026, sera — **il prodotto vero, un video 4K, e un filo a 10 Mbit/s**

> *«Sono dentro. Sto riproducendo un video di YouTube a 4K. **Perfetto**.»*
>
> *E poi, dopo aver strozzato lui stesso la banda del tablet:*
>
> *«Il video mostra degli artefatti, ma è normale: **siamo sotto le specifiche**. Però **audio e
> video fluidi e in sync**.»*

⭐ **La prova se l'è disegnata lui.** Alla proposta di strozzare a 30 Mbit/s è stato messo davanti il
numero — `[M]` quel video viaggiava a **6,0 Mbit/s**, cioè trenta sono **cinque volte** quel che
serve — e ha risposto **scendendo a 10** e strozzando ⭐ **il tablet**, non il server: cioè
**il percorso vero**, dal lato del client, che è la scena che un utente vero produce.

#### `[M]` Le due misure, prese dal registro **senza toccare la sua sessione**

| | filo libero | ⭐ tablet a 10 Mbit/s |
|---|---|---|
| **fotogrammi consegnati** | 38,5/s | ⭐ **37,4/s** — *praticamente uguali* |
| **byte a fotogramma** | 19 377 | ⭐ **10 680** — **la metà** |
| **banda** | 6,0 Mbit/s | ⭐ **3,20 Mbit/s** — **la metà** |
| **la coda sul filo** | vuota | ⭐ **vuota** — `arretrato massimo 0, posti 2` |
| **il motore che COMPONE** (`rcs0`) | 41,3 % | **45,6 %** — *la scena si muove come prima* |

⇒ ⭐⭐⭐ **Non ha rallentato: ha compresso di più.** Ha **dimezzato la banda senza perdere un
fotogramma** e senza mettere niente in coda — ed è alla lettera il secondo principio di
`SPECIFICHE.md`: ⭐ *«degradare, non fallire»*.

⚠ E il margine che gli restava: **3,2 su 10 Mbit/s**, cioè il **32 %** del filo concesso.

> ### ⛔ E UN NUMERO CHE STAVA PER DIVENTARE UN DIFETTO CHE NON C'È
>
> Il primo colpo d'occhio, **mentre il video si stava rimettendo in moto**, diceva **14,0 fot/s e
> 0,17 Mbit/s**: sembrava un crollo, e con la coda vuota sembrava pure *«il prodotto si trattiene
> da solo»*.
>
> ⛔ **Non lo era: era il transitorio.** ⭐ **Il testimone che l'ha smascherato è il motore di
> disegno** — a **45,6 %**, cioè **la scena si stava muovendo eccome**. ⇒ Il calo non poteva essere
> «non c'è niente da mandare».
>
> ⭐⭐ **La regola**: prima di attribuire un calo al prodotto, si guarda **quanta sollecitazione sta
> arrivando** (`LEZIONI.md` §1.30). Qui la sollecitazione c'era, e la spiegazione era **un'altra
> ancora**: il video non aveva ancora ripreso a scorrere.

#### ⭐⭐ E questo giudizio chiude un `[?]` della FASE 9

`fasi/09-la-qualita-e-la-degradazione.md` lasciava aperta la metà **AV** del sincronismo — *«non è
rimisurata: vuole quel browser»* — ⛔ **e quel browser non partiva** (§20.1-ter, ora refutata).

⇒ ⭐ **Adesso è stata giudicata**, sulla scena più dura che ci sia — **un video 4K su un filo sotto
le specifiche** — e il verdetto è dell'utente: **«audio e video fluidi e in sync»**.

⚠ **E la parola che conta è la sua**: *«artefatti, ma è normale: siamo sotto le specifiche»*.
⇒ ⭐ **Non è indulgenza: è il metro giusto.** Il prodotto non ha promesso 4K a 10 Mbit/s; ha promesso
di **non mentire e non sbriciolarsi**, e sotto il pavimento dichiarato ha consegnato **artefatti
visibili con la fluidità e il sincronismo intatti** — cioè ha speso il poco che aveva **dove
l'utente se ne accorge di meno**.

### ✅⭐⭐⭐⭐⭐ **LO SCOPO È RAGGIUNTO — il multi-tenant**

> *«Allora la sessione ha raggiunto il suo scopo: il multitenant. **10 utenti contemporaneamente
> presenti su una GPU integrata è un risultato di assoluta eccellenza**.»*

⭐ **È il giudizio che chiude la fase**, e cade esattamente sul suo scopo dichiarato — *«più utenti
insieme, il budget, il rifiuto motivato»* (`PIANO.md`, fase 10).

`[M]` **I numeri su cui è stato dato**, e sono tutti misurati su sessioni che **disegnavano davvero**
— fotogrammi contati e GPU letta:

| | undici desktop veri insieme |
|---|---|
| quanto peggiora **chi già lavorava** | ⭐ **−7,7 %**, sotto la tolleranza |
| il **ritardo** | ⭐ **non si muove**: 8,4 → 8,0 ms |
| violazioni di **I1** (*«mai peggiorare chi c'è già»*) | ⭐ **zero su undici** — contro **37** sulla scena satura |
| quanto costano alla GPU | ⭐ **22-24 %**: poco meno di **un quarto** della macchina |

⇒ ⛔ **Il soffitto non è stato trovato: sono finiti gli utenti, non la macchina.**

⚠ **E l'aritmetica accanto, dichiarata come aritmetica e non come scena provata**: dieci che lavorano
≈ **23 %**; più **uno** che guarda un 4K a schermo intero ≈ **64 %** (ci sta); più **due** ≈ **105 %**
(il bordo). ⇒ ⭐ *Dieci normali più uno o due video reggono; tre video a schermo intero no.*

### ✅⭐⭐⭐⭐⭐ **E IL PRODOTTO È STATO GIUDICATO ANCHE SOTTO LE SPECIFICHE — 25 agosto 2026**

> *«Sono soddisfatto. Riprodotto audio e video su una connessione del 1990. **Non credo che si possa
> chiedere di più**.»*

⭐⭐ **«Una connessione del 1990» è una sua parola, e torna da lontano**: alla fase 9 aveva corretto il
bersaglio dicendo *«30 mbps sono una connessione da metà anni 90»* (`DECISIONI.md` §3.1-ter) — ⇒ e
oggi ha portato il prodotto **a un terzo di quella**, con un **video 4K** dentro, e l'ha giudicato
**sufficiente**.

⛔ **Ed è il metro giusto, non un abbuono.** *«Non credo che si possa chiedere di più»* non dice *«è
perfetto»*: dice ⭐ **«ha speso bene quel poco che aveva»** — che è esattamente quel che
`SPECIFICHE.md` §2 promette e quel che §4.6-decies ha appena messo per iscritto.

---

## §10-bis · Le due decisioni NON prese — **e restano aperte, con i predefiniti in vigore**

⛔ **La fase si è chiusa senza che venissero decise, e questo si scrive invece di arrotondarlo.**
⭐ Non sono state dimenticate: gli sono state messe davanti **tre volte**, e ha chiuso prima.
⇒ ⚠ **Quel che vale oggi è il predefinito**, e chi riaprirà la questione parte da qui.

| | che cos'è | ⚠ che cosa vale **oggi** |
|---|---|---|
| **QVBR** — il tetto di banda per sessione (§8.2, **P7**) | la cura della fase 9: `[M]` **esiste, funziona, obbedisce entro il 5 %**, e copre **8,8×** di banda | ⛔ **SPENTA.** Il predefinito è a qualità fissa |
| **i numeri di fabbrica** | `--tetto-sessioni` e `--riserva` | **10** e **0,5** — `[M]` a 0,5: **0 falsi sì, 0 falsi no** |

> ### ⭐ E la fase ha portato un argomento NUOVO su QVBR, che prima non c'era
>
> `[M]` **Il prodotto ha dimezzato la banda da solo** — 6,0 → **3,20 Mbit/s**, senza perdere un
> fotogramma. ⇒ ⭐ **QVBR non serve a un utente solo**: il regolatore fa già il suo mestiere.
>
> ⛔ **Serve quando gli utenti sono dieci** — un tetto **per sessione** è quel che impedisce che
> dieci si prendano il filo del server tutte insieme. ⇒ È la domanda che `DECISIONI.md` §3.1-bis
> punto 2 aveva lasciato aperta — *«dieci sessioni × 30 Mbit/s sono 300 Mbit/s sul filo del
> server»* — ⛔ **e che questa fase NON ha misurato**: i clienti giravano sulla stessa macchina, su
> `lo`. Il filo è **contato, non provato** (§9).

---

## §10-ter · *(il posto del giudizio, come era stato preparato)*

*(la fase si chiude qui, e non prima)*
