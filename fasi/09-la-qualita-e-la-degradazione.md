# Phase 9 — Quality and degradation

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

Opened on **23 Aug 2026** · ✅ **Closed on 24 Aug 2026**, on the user's judgement:
*«il prodotto cambia in meglio; questa fase era per rendere più solido il funzionamento di remotix su
reti degradate, senza pretendere di fare miracoli»*

> ⛔ **This document fills up as we go** (`PIANO.md` §0.1). The measurements carry the time
> beside them because they were written when they were taken.

> ## 📖 WHERE THE SEVEN DOCUMENTS OF 23 AUG WENT
>
> ⛔ **They were merged here and deleted**, and that is the project's rule: *few large
> documents; the agents' reports are not kept.* ⚠ **Some comments in `src/` and in `banchi/`
> still cite them by name** — this table is what you need to follow those references.
>
> | the file that no longer exists | where it is now |
> |---|---|
> | `09-il-crollo.md` §1 · §2 (the proof, the log) | **§4.2** |
> | `09-il-crollo.md` §3 (the suspects ruled out) | **§4.3** |
> | `09-il-crollo.md` §4 (the cause) | **§4.1** and **§4.4** |
> | `09-il-crollo.md` §5 (how to reproduce it) | **§4.5** and **P1** |
> | `09-il-crollo.md` §6 (the trap) · §7 (the cure) · §8 (`[?]`) | **§4.7** · **§4.6** · **§4.8** |
> | `09-proposta-sgombra.md` §1-§4 (the mechanism, the threshold, the edge cases) | **§5.2** |
> | `09-proposta-sgombra.md` §5 (the prediction) · §6 (the partial refusal) | **P2**/**P3** · end of **§5.2** and **§10.2** |
> | `09-proposta-cricchetto.md` §1-§3 (the defect, the cure) · §4 (the bench) | **§5.3** · **§7.3** and **P5** |
> | `09-proposta-riordino.md` §1-§5 · §7 · §8 (the frontier, the price, the honest question) | **§5.4** |
> | `09-proposta-riordino.md` §6 (the prediction) | **P6** |
> | `09-studio-bitrate.md` §0-§3 (the modes, the cap) · §4 (the level) | **§5.5** and **§10.1** |
> | `09-studio-bitrate.md` §5 (the prediction) | **P4** and **§10.1** |
> | `09-disegno-regolatore.md` (all of it) | **§6**; the prediction in **P7**/**P8**, and §5.3 in **§6.5** |
> | `09-il-registro-delle-discese.md` (all of it) | **§7** |
>
> ⭐ And where the document repeated a comment in the code, **the code stayed**: the seat of the
> reasoning is `src/`, and here there is the `file:line`.

---

## What it must produce

**Rate control**, the **degradation ladder**, the behaviour on a **bad network**.

> ## ⛔⭐⭐⭐ THE TARGET WAS CORRECTED BY THE DIRECTOR — *23 Aug 2026, evening* → **§17**
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».* — `DECISIONI.md`
> **§3.1-ter**.
>
> ⛔ **Bandwidth leaves the body of the phase**, and the reason is a measurement of this very phase: §16,
> on the **real path**, the worst case asks for 21.5-23.1 Mbit/s and the product holds it **without
> degrading and with all the cures off**. A bench that cannot make what it measures give way is not
> measuring the right quantity.
>
> ⭐⭐⭐ **And on the right quantity the product gives way, and gives way very early** (§17.1, §17.11):
> ⛔⛔ **the step is DOUBLE** — the keyframe spiral starts **at the first lost packet**
> (0.00-0.10 % of real loss), the drop the user **sees** falls five times further on
> (0.53-0.75 %): ⇒ between the two there is half a percentage point in which the product **is already degenerating and
> the frames per second still say everything is fine**. ⚠ And near the edge it is **bistable**:
> same input, `0 chiavi · 40,16/s` **or** `24 chiavi · 33,84/s`; with **zero loss** and ±15 ms of jitter **16.6/s and DOUBLE the bytes on the
> wire**, which is the direct proof that disorder is mistaken for loss; at **13 %** in
> bursts ⛔⛔ **the session detaches after 0.3 s**, and *«mai staccare»* is the only obligation that holds
> everywhere.
>
> ⭐⭐⭐ **AND THE CURE WORKS** (§17.6, paired with three arms): the keyframe share goes from
> **51.7-88.1 %** to **0.0-5.6 %**, the rate comes back **by 1.7 to 2.8 times**, and the bytes on the wire
> **rise** — ⇒ the line was not saturated, **it was wasted**. ⛔ But **both** cures are needed: the
> threshold alone leaves 12.8-33.6 % keyframes. ⚠ **The healthy line pays nothing** (39.85 / 40.19 /
> 39.63 frames/s, zero keyframes), and the price is **from −38 to +161 ms** of delay on the ordinary
> profiles — **4.5 s** on `raffica-forte`, where *«immagine che si muove con cinque secondi di
> ritardo»* against *«immagine ferma»* **is not a choice that belongs to a measurement**.
> ⇒ ❓ **The cures stay OFF**: I6, and the decision is the user's.
>
> ⭐⭐ **And the audio reorder cure BITES** (§17.2): purity from 0.40-0.80 to **1.0000** on
> all five profiles that reorder, six out of six green.

**What the user sees and judges at the end**: ⛔ **the image, and that's all.** In v1 the homologous phase
was validated with PSNR and SSIM, the user's judgement on the real desktop was *«siamo tornati
indietro»*, and the phase was **reset to zero**.

---

# ⭐⭐⭐ THE SUMMARY — *the day of 23 Aug 2026*

> ⛔ **This is the head of the document: it answers quickly the four questions that will be asked
> tomorrow.** The details, with the times and the scenes, are below: §0 the opening study, §1 the bench,
> §3 and §3-bis the measurements, §4 the crash, §5 the cures, §6 the work that remains, §7 the predictions,
> §8 what did not work, §10 the contradictions.
>
> ⛔⛔ **AND ON THE EVENING OF 23 AUG THE CURES WERE MEASURED: it is in §13, and it changes six lines of
> this summary.** In two words, and the details there:
> ⭐⭐⭐ **the memory cure HOLDS** and the crash reproduces **two times out of two**, with the stack
> read from the core (§13.1) · ⭐⭐⭐ **the rate regulator switches off the spiral**: zero keyframes and zero
> abandons where before there were 18 and 24 (§13.3) · ⛔ **the threshold alone does NOT keep what
> P3 promised**, and it must be tuned **the opposite way** from what P3 said (§13.2) · ⭐⭐ **the bandwidth
> cap survives its two reds** (§13.4) · ⛔⛔ **all the bandwidth numbers of §3.8 are
> HEVC, and the product sends H.264**: same scene, **21.18 against 7.92 Mbit/s** (§13.5) ·
> ⛔⛔ **4K holds 41 fps, not 60**, and the produced level **exceeds** the client's
> (§13.6) · ⭐⭐⭐ **§10.2 is decided: the spiral on the real desktop does not bite down to 10 Mbit/s**
> (§13.8).
>
> ⛔⛔⛔ **AND ON THE NIGHT OF 23 AUG THE YARDSTICK CHANGED: §14, and from there down the numbers are
> H.264.** ⛔ The test client negotiated HEVC because of a line left three days behind;
> now it negotiates **what Firefox negotiates**, verified on the lines of `pagina.html` (§14.1).
> In two words: ⛔⛔ **the hard case in H.264 still asks for 44.6 Mbit/s = 223 % of the floor** —
> the cap is needed (§14.2, §14.3) · ⛔ **the HEVC/H.264 ratio is NOT a constant**: 0.36× on the
> halftone, 0.76× on the grain, ⛔ **1.7× and up** on the real desktop (§14.2) · ⛔ **the threshold alone
> does not keep the promise at ANY value**, and at 800 ms it pays **1 321 ms** of queue; ⭐ the lever is the
> **pair** with `--ritmo-adattivo` (§14.4) · ⭐⭐⭐ **P8 is GREEN**, in still/moving pairs in the
> same round (§14.5) · ⭐ **4K in H.264** and ⛔ **audio** in §14.6 and §14.7.

## S.1 · ⛔ The most serious fact of the day: **the product died, and the cause is proven**

At **08:28:09** the 7900 server died of `SEGV` on frame **185**, a delta of
**525 298 bytes**. ⭐ **The cause was found line by line**: `wt_scrivi()` freed the bytes of
a frame as soon as ngtcp2 had **serialized** them, while the contract of
`ngtcp2_conn_writev_stream()` requires keeping them **until the ack**. ⇒ **Use after free**, and
the defect was there **on every retransmitted frame, always**: the 525 KB one was only the
first **large** enough for `free()` to really return the pages to the kernel
(`1` `mmap` block out of **45 005** in that round). Below 128 KiB the same error sent the client
**garbage bytes in silence**. ⇒ §4.

⭐ **The cure is applied** (`src/webtransport.c:745-870` and `:5929`): at `wt_scrivi()` nothing is freed
any more — it is marked `consegnato`, and freeing is done by the ack (`coda_conferma()`) or by the closing of the stream.
⛔ **It is not behind a switch**: it does not change what is seen, it corrects a way of dying.

## S.2 · What was measured, and what it is worth

| | `[M]` 23 Aug | where |
|---|---|---|
| ⛔ **with a still scene the rate does not drop: IT STOPS** — 1 frame in 30 s, then zero. And **it is not ours**: Mutter delivers only on change (123 empty waits/s) | 0.03 fps, repeated 2 times, reconfirmed at 2560x1080 | §3.1 |
| ⭐⭐⭐ **and waking from still costs NOTHING** — 180 shots, quiet from 0.2 to 15 s | **13 ms** median, **all** 180 measurements between **12.3 and 14.3** | §3.6 |
| ⇒ and **80 % of those 13 ms is waiting for the compositor**; encoding, which is ours, is worth 2.7 of them | 10.2-10.9 · **2.6-2.7** · 0.0 | §3.6 |
| ⭐ **the user's REAL desktop, full screen and moving, costs 1 % of the floor** | **0.204 Mbit/s**, found again twice (0.193 · 0.195) | §3.8 · §3.15 |
| ⛔ **but the hard case asks for THREE TIMES the floor** — a film with grain at full screen | **58.668 Mbit/s = 293 %** of 20 | §3.8 |
| ⛔ **and «how many pixels change» predicts nothing**: bandwidth depends on CONTENT | `pieno` 1.2 · `barra` halftone **21** · grain **59** Mbit/s, with the same pixels moved | §3.8 |
| ⛔⭐ **a 3-second hole is enough** to bring the rate from 40 to 13/s and make half of them keyframes | and `abbandoni §5.1` = `chiavi`, **one to one**, at every level | §3.10 |
| ⭐ **but the return is immediate and there is no hysteresis**: full regime the second after | 42 fps, **0 keyframes**, no aftermath in 17 s | §3.10 |
| ⭐ **the three morning cures changed nothing where they should not have** — paired comparison 7900/7910 | wake-up ±0.5 ms · `pieno` **164 bytes out of 3.62 MB = 0.005 %** | §3-bis |

## S.3 · What changed in the code, and behind which switch

⛔ **Six cures, and four of them are OFF from birth (I6).** The diff is not here: it is in `src/`,
and the comments in the code are the seat of the reasoning.

| # | the cure | where | switch | verified? |
|---|---|---|---|---|
| **1** | ⛔⭐ **the crash**: freeing happens at the **ack**, not at serialization | `webtransport.c:745-870`, `:5929` | ⛔ **none** — it is the correction of a defect | ⛔ **no**: the recipe of §4.5 was not run |
| **2** | **the queue threshold** in `video_sgombra()`: a delta is abandoned only if the queue does not empty within the threshold | `webtransport.c:2705-2800` | `--sgombra-soglia-ms N`, **0 = off** | ⛔ no |
| **3** | **the quality climb-back**: `qualita_corrente` was a one-way ratchet | `codificatore.c` (`risali_qualita()`), `:141-143` | `--qualita-risale`, **off** | ⛔ no |
| **4** | **the audio reorder**: discarding happens on *«already consumed»* (§6.3), not on *«already arrived»* | `pagina.html` · `avvia_audio()` (`audio_posto_passato`), `:5992`, `:6507` | ⛔ **none** — it is a pure loosening, it does not add a ms | ⛔ **no, and the bench CANNOT see it** — §3.16 |
| **5** | **the bandwidth cap**: `QVBR` with wire, working point and reservoir derived from the floor | `codificatore.c:200-340`, `:1786-1800` | `--tetto-banda-mbit N`, **0 = off** | ⛔ no on the test machine (yes on the laptop) |
| **6** | ⭐⭐ **the rate regulator**: a frame does not leave when **2 deltas** in flight still have bytes in our queue | `webtransport.c` — `ritmo_frena()`, `ritmo_ciclo()`, `wt_ritmo_adattivo()`; the call is in `video_a_una()` **before** `video_sgombra()` | `--ritmo-adattivo`, **off** ⛔ **and it is not enough on its own: see below** | ⛔ no — no measurement, only the prediction written in the code |

⛔⛔ **AND CURES 2 AND 6 ARE TWO SWITCHES THAT DEPEND ON EACH OTHER — it is written here
because it is the easiest fact to measure wrongly in the whole phase.**

With `--sgombra-soglia-ms 0` (the default) `video_sgombra()` abandons every delta that still has
bytes in the queue, at every more recent frame. ⇒ When frame N+1 arrives, the only delta that
can still have our bytes is N: **`arretrato` is 0 or 1, never 2, by construction** — and with
`WT_RITMO_POSTI = 2` the regulator **never fires**.

⛔ A bench that turned on only `--ritmo-adattivo` would measure **zero descents** and would read *«the
line carries it»*. They are two facts with the same face. ⇒ The regulator is tested **with both
on**:

```
remotix --sgombra-soglia-ms 100 --ritmo-adattivo
```

⭐ And the server **says it at startup** instead of leaving it to be deduced: `wt_ritmo_adattivo()` is called
*after* `wt_sgombra_soglia()` on purpose, so it reads the value **in force**, and with the threshold off
it writes `⛔⛔ MA LA SOGLIA DELLA CODA VIDEO E' SPENTA … questo regolatore NON SCATTERA' MAI`.
⚠ The order of the two calls in `main.c` is part of the cure: inverting them would make it read zero, and
that line would say the false thing precisely in the round where it is needed.

⭐ **And a sixth thing, which is not a cure but shows in the log**: the values **in force** are now
written at startup — `PARAMETRI IN VIGORE`, `la scala della degradazione` (26 → 35 → 44 → 51),
`risalita della qualita' SPENTA`, `LIVELLO PRODOTTO`, `il client dichiara video.livello`. ⛔ Until
this morning the comparison of `RCP.md` §4.3 **could not be made from outside**: one of the two numbers was
not written anywhere. The check is in §3.12, and the 7900 has none of those lines.

## S.4 · ⛔ What was tried and does NOT work

1. ⛔⛔ **The bench prescribed for audio cannot see cure 4, and the number proves it.**
   `07-b64-rete.py` measures the **transport**; the cure lives in the **page**. The test client has
   **its own** copy of the old rule (`01-b3-cliente.py` ⚠ *(the cited code is no longer there: to be reread)*), identical byte for byte in the two
   trees (`md5 13e68d19…`). ⇒ The prediction *«0.175 → ≥ 0.95»* came out **0.1149 → 0.1235**, that is
   nothing — ⛔ **and it does not refute the cure: it refutes the bench.** §3.16;
2. ⛔ **`VBR` is out, and not by opinion**: under VBR the `qp` is **ignored** — with and without `qp=26`
   **the very same bytes** come out, two times out of two. ⇒ The whole degradation ladder and the
   climb-back written this morning would become **silent no-ops**. **QVBR** was chosen, where the
   ladder holds (`codificatore.c:200-215`);
3. ⛔ **This morning's bench measured an OVERVIEW.** The headless GNOME session sits
   in the Overview and stays there: *«full screen»* was **a shrunken preview**, and the bytes of
   §3.1–§3.3 are those of **a fraction of the screen**. Found **by looking at the pixels**, not at a
   counter. §3.7;
4. ⛔⛔ **Eight bench stumbles in one day, and six out of eight produced «a plausible
   number», not a red** — the orphan stage that accused three innocent cures, the `ESC` that
   switches off what it was supposed to switch on, the `UID_B` that kills the other user's Firefox, the
   `wc -l <` that reads zero. §8;
5. ⛔ **The quick route for the crash is wrong**: `shutdown_stream_write()` before the `free`,
   as `video_sgombra()` does, *resets* the stream — and §6.2 wants the **complete** frame.
   It would be trading a rare crash for a broken frame **always**. §4.6.

## S.5 · ⏳ What remains, in what order, and **why that order**

| | why before what follows |
|---|---|
| **1.** ⛔ **reproduce the crash with the recipe of §4.5** (`MALLOC_MMAP_THRESHOLD_=32768` + frozen client), and arm the trap of §4.7 | ⛔ The cause is *probable with the line*, **not seen in flight**. And until it reproduces, one cannot even prove that the cure cured it: one would be measuring an absence |
| **2.** ⭐ **measure the five cures on the real hardware**, one at a time, paired | ⛔ They are **five variables**. The method of §3-bis (two servers, «before» alive beside «after») is already written and has already caught a false alarm for the queue |
| **3.** ⛔ **write the bench that runs the PAGE** for cure 4 | Without it, the audio cure stays **unverifiable**: today's bench measures itself. The shape of the bench is already written in §3.16 |
| **4.** ✅ **the rate regulator** — **written** on 23 Aug 2026, cure 6 of S.3, ⏳ **not measured** | ⛔ The mandatory order was respected: cure 2 (`--sgombra-soglia-ms`) is its prerequisite and arrived first. ⚠ **And the trap remains**: switched on alone it never fires, and the server writes so at startup — see S.3 |
| **5.** ✅ **the descent log**, §7 | It is born together with the regulator, not after: **two lines per episode** (`il ritmo SCENDE` / `il ritmo RISALE`), never one per frame; every descent carries **the measurement beside the threshold** (`arretrato N contro 2 posti`), plus `cwnd`, `cwnd_left`, bytes in flight and the queue inside the network in ms. ⏳ The **tuning of `POSTI`** on the bench remains |
| **6.** ⛔ **the user's judgement on the two things that change what is SEEN** | It is the only thing that closes the phase, and it is the lesson paid for with the reset of phase 10 of v1 |

⛔⛔ **And the THREE things that wait for him, explicitly:**

| | the price, quantified |
|---|---|
| **the queue threshold** (`--sgombra-soglia-ms 100`) | dragging a window while the line drops, the window follows the pointer with up to **~150 ms** of delay for a moment (**~205 ms** from gesture to pixel, adding the loop of phase 8) — ⛔ **instead of jumping from one image to the next at keyframe rate**, which is what it does today. ⚠ Which of the two is worse **is not decided by a measurement** |
| **the bandwidth cap** (`--tetto-banda-mbit 20`) | on the **hard case** the image gets uglier: that is its job. ⭐ On **real content** the prediction is that **nothing happens** (0.204 Mbit/s, 1 % of the floor) — and if the real desktop cost **less** than before, the cap is saving where it must not and **the cure is thrown away** |
| **the rate regulator** (`--ritmo-adattivo`, with the threshold on) | during a line drop **fewer frames are seen**: movement becomes jerky instead of old. ⭐ The prediction is that **at 20 Mbit/s it does nothing** — it is a **parapet**, and its correct behaviour is to do nothing. ⛔ If one day the delivered scene goes **below 25/s on a 20 Mbit/s line**, the log declares it a **defect** and does not fight it: forcing a frame into a queue that does not empty makes the queue worse |

## S.6 · ⛔⛔ THE TWO CONTRADICTIONS, declared and not smoothed over

⚠ **They are in full in §10, with what would decide them.** In short:

1. ⛔ **«No bandwidth cap is needed» (morning) against «it asks for 293 %» (afternoon).**
   The 09:07 study concluded *«on the measured content, at 20 Mbit/s, CQP 26 is just fine»*
   on the basis of `[M]` phase 8 (24 956 bytes per keyframe, 4.17 Mbit/s in the worst regime). At 08:35
   UTC the film with grain at full screen gave **58.668 Mbit/s**. ⇒ ⭐ **They do not contradict each other
   on the number: they measure two different contents**, and the study had written so (*«the user's
   desktop does NOT contain that scene»*). ⛔ **What was refuted is its estimate**: ~19.9
   Mbit/s extrapolated from v1, **optimistic by three times**;
2. ⛔ **How much the spiral bites above the floor — two positions.** The threshold proposal
   (§5.2) maintains that the defect **lives below the floor** and that above it the cure is **inert**
   (`[M]` at 15 Mbit/s: 2 keyframes out of 1 019). The step of §3.10 shows abandons and keyframes **even
   on the wide line** (3↔3, 1↔1 at 22-26 Mbit/s). ⇒ The two positions are not decided yet, and
   §10.2 says with which measurement they are decided.

---

## §0 · THE OPENING STUDY — *23 Aug 2026*

Read in full `RCP.md`, `SPECIFICHE.md`, `DECISIONI.md`, `LEZIONI.md`, `STUDI.md`, `PIANO.md`,
`CODER.md`, the three documents of phases 6/7/8, the v1 documents and the rate code. Four agents
in parallel, extraction mandate. What follows is the **result**, not the story.

### 0.1 ⛔⛔ A CORRECTION OF NOMENCLATURE, first of all

**In v1 the wounds are TWO different phases, and the V2 documents confuse them.**

| | v1 phase **9** | v1 phase **10** |
|---|---|---|
| what it was | zero copy, the CPU milliseconds per frame | **quality and bandwidth** |
| the error | CPU optimized while the delivered frames **dropped** (29→22.7) | validated with **PSNR/SSIM** instead of with the user's eye |
| the outcome | a lesson | ⛔ **RESET TO ZERO**, code brought back, benches removed |

⇒ ⭐ **Phase 9 of V2 is the heir of phase 10 of v1.** `PIANO.md:1180` writes *«in v1 this phase
had been validated with PSNR»*: it is true as a *homologous phase*, ⚠ but whoever looked for «phase 9» in
`LEZIONI.md` would find **the wrong wound** (the CPU). `LEZIONI.md` §2.4 and §7.2 and
`DECISIONI.md` §3.2 correctly say **phase 10**.

### 0.2 ⛔ The exact account of the reset — `fondamenta/documenti/PIANO.md:1410-1442`

> *«La fase 10 va azzerata e ricominciare da zero.»* — The code went back to the closing state
> of phase 9. **The benches were removed.**

⛔ **`fondamenta/documenti/PIANO.md:1418`: «the error was not technical».** The three reasons, verbatim:

1. **A change to what is seen was shipped to whoever watches, validated only on the bench.** The
   switch to **VBR** had PSNR, SSIM and a still frame looked at by eye; **it did not have the
   user's judgement on the real desktop, which is the yardstick**;
2. **It was optimized in the wrong direction.** «Spending less bandwidth» was a gain; for the
   product bandwidth is a **floor**, not a budget. ⇒ ⛔ **Half the measurements were right and
   answered the wrong question**;
3. **The state of the machine was not checked before starting** — the user took a known defect
   in the face in the middle of the day.

⭐ **The technical fact that triggered everything** (`fondamenta/documenti/SPECIFICA.md:93-96`): the bitrate
control shipped *«on a barely moving desktop dropped to 2–6 Mbit/s, happy to save»*. ⚠ And
the text of the specification **lent itself to the opposite reading** — that is, a phase was reset to zero
also because of **the ambiguity of one line of specification**.

⭐⭐ **What was NOT thrown away**: the measurements with date and source, and the user's decisions —
adaptive resolution **out**, AVC444 **out**, encoding by regions **out**.

### 0.3 ⛔ THE MOST SERIOUS FACT — **today quality is not governed at all**

`[R]` 23 Aug 2026, read in the code:

| | today |
|---|---|
| video **bitrate** control | ⛔ **does not exist**: `grep bit_rate\|maxrate\|bufsize codificatore.c` → **zero occurrences** |
| **QP** | `figlio.c` · `scatto_chiudi()` `QP_HARDWARE 26` **fixed**, `rc_mode = CQP` — and the comment declares it: *«the value is a convenience: the working point between quality and bandwidth is phase 9»* |
| **congestion** algorithm | ⛔ **never chosen**: `grep cc_algo\|NGTCP2_CC` → **zero**. ngtcp2's default is taken |
| the **only** loop reacting to bandwidth | `webtransport.c` · `wt_video_gancio()` `chiave_intervallo_ms()` — it rules **how often a keyframe can be REQUESTED**, not how much a frame costs |
| the degradation the product **really has** | `webtransport.c` · `WT_TIENILA_VIVA_NS` `video_sgombra()` |

⛔⛔ **And `video_sgombra()` goes the opposite way from what §3.3 asks.** Called at **every**
frame (`webtransport.c` · `wt_ritmo_adattivo()`): on a narrow line a delta does not get out in 33 ms, so it is
abandoned **always**; every abandon rekindles the debt of `RCP.md` §5.2 (`rcp.c` →
`:3382`) ⇒ the stream degenerates into **keyframes only**. ⇒ **It degrades in space AND in time together**,
instead of lowering the rate while keeping the deltas. ⭐ The cure is **named in the code**, allowed by §5.1,
and **was never written**: abandon a delta only when it is *really hopeless* — a
threshold on the queue.

### 0.4 The rules that bind, and that are not put back into question

| | |
|---|---|
| **I1** (`SPECIFICHE.md` §8.2) | *«The rate never drops out of prudence, to save, or because the scene is still. It drops only when the measurement proves that the line does not carry it, and every descent is declared in the log.»* |
| **§8.3** | ⭐ **FRAMES are dropped. Never blur, never detach.** Degrade in time, not in space: text stays readable. And at a low rate **more** bits are spent per frame |
| **I6** | whatever changes what is SEEN stays **behind a switch that is off** until the user has looked at it — ⛔ it is the lesson paid for with the reset |
| ⛔ **delay weighs more than frames** (`SPECIFICHE.md:128`) | *«every intermediate buffer buys smoothness and sells response»* ⇒ **every cushion this phase wanted to add must be justified against this line** |
| **§3.1-bis** (new, 23 Aug) | ⭐ **the line floor is 20 Mbit/s** |
| **§2.1** (confirmed on 23 Aug) | ⭐ **the image floor is 480p · 25 fps**, and it is now the **bottom of the ladder**: below it, the regulator has no permission to go down |

⛔ **The ladder is one-dimensional by decision**: the other levers are closed, each with its own
line — **resolution** (`DECISIONI.md` §5.0-ter, deliberately out), **the canvas** (not touched
with a live session, §5.1-bis), **4:4:4** (postponed to RCP/2), **depth** (negotiated, not
degraded). What remains is the **qp**, for which no ladder is defined.

### 0.5 ⭐ The numbers already in hand — we do not restart from zero

| | `[M]` |
|---|---|
| at **3 Mbit/s with a MOVING desktop** audio passes 397 blocks out of 6 458 — purity **0.18** | 21 Aug |
| at **3 Mbit/s with a STILL desktop** — purity **1.000** ⇒ ⛔ **it is not the bandwidth: it is the video** | 21 Aug |
| with **Opus** (1/32 of the audio bandwidth) **58 %** is lost anyway ⇒ reducing what audio asks for **does not save it** | 21 Aug |
| on the narrow rounds the delivered frames are **all keyframes** (144/144, 149/149) against **2 out of 1 019** at 15 Mbit/s | 21 Aug |
| a 60 KB keyframe at 3 Mbit/s occupies the window for **160 ms**, and `WT_CHIAVE_RICHIESTA_MS` grants one every **150** | 21 Aug |
| ⛔ **four transport variants change nothing** (397 · 278 · 406 · 514 · 371) ⇒ *«the window is not contended: it is already full»* | 21 Aug |
| the **hardware encoder floor** (v1, R31): asking for 2 000 kbit/s at moving 1440p, out come **3 702 (VBR) · 3 966 (CBR) · 4 111 (QVBR)** (the comparison with `libx264` no longer holds after phase 18) ⇒ **there is a bottom around 4 Mbit/s, and from there down the only lever is fewer pixels or fewer frames** | v1 |
| ⛔ **the bitrate control mode is not chosen: the driver DEDUCES it** (`rc_max_rate == bit_rate` ⇒ CBR, and nobody had chosen it) | v1, R31 |
| on a still desktop CBR spent **9 875 kbit/s against 277 for QVBR, for 1.8 dB** ⇒ *«the choice is not played on the hard scene: it is played on how much is spent when it is not needed»* | v1, R31 |
| the rate of the **user's real content**: **20.9 frames/s**, 31 % identical | phase 8 |
| the real weight of keyframes on the user's canvas: max **21 433 bytes = 0.13 %** of the 16 MiB cap | phase 8 |

---

## §1 · THE BENCH — *written BEFORE developing*

*The rules, fixed before measuring. The three benches born from them are in §1.1 and §1.2.*

- ⭐ **the working point is 20 Mbit/s and above** — `DECISIONI.md` §3.1-bis. Below, one may *look*
  but does not *promise*;
- ⭐ **the REAL path is throttled, not `lo`**: `wondershaper` is in `~/.local/bin` on the user's
  tablet. ⚠ It is the declared limit of `banchi/07-b64-rete.py`, whose `netem` half runs on
  `lo`, where the MTU is 65536;
- ⛔ **the deciding check already exists**: `banchi/07-b65-datagram.py --scena no`. A bench that with a
  still scene does not give purity 1.000 has measured nothing;
- ⛔ **the first check of the phase is INVARIANT I1**: that the rate does **not** drop with a still scene;
- ⛔ **all three quantities are measured** — CPU ms · frames/s · **delay** — **plus the
  outgoing bytes**, and the work is fixed before the comparison (`LEZIONI.md` §6.2, §1.26);
- ⚠ **PSNR/SSIM may be used as a working tool, never as a verdict**, and first they are
  certified against the three traps of `fondamenta/documenti/REFERENCE.md:2437` (the muxer's fps, the
  scene that ends before the clip, the chroma not exercised).

⚠ **Cleanup before measuring**: four agents' test servers were left running as root
(**7746, 7752, 7765-67, 7775**), and ⛔ **two do not measure on the same machine**
(`LEZIONI.md` §1.26: it does not give a red, it gives **a plausible number**).
✅ *Closed on 23 Aug*: after the reboot and the reprovisioning the machine has **a single 7xxx port
open, 7900** — verified with `ss -tuln` before measuring.

### 1.1 ⭐ THE FIRST BENCH — `banchi/09-b68-ritmo.py`, *23 Aug 2026*

**The question, only one**: on a **wide line** — no throttling, the case in which I1 has
no excuse — **does the rate drop when the scene is still?**

| | |
|---|---|
| **the session** | `banchi/01-b3-cliente.py` **inside the container** (`enter.sh --root`): `aioquic` is there, not outside. It is the job of `07-b65-datagram.py`, not a new route |
| **the scene** | `04-b30-scena` already built, in three states: **still** (no scene) · **bar** (a scrolling bar) · **full** (bands at full screen). ⛔ It wants the monitor **by name**, and the name is told by the log (`monitor «Meta-0»`) |
| **the stage** | it is born with the **first** client and survives the detach (I4) ⇒ without a session opened before, `--uscita` finds no monitor |
| **the frames, keyframe against delta** | from the per-frame line `rcp.c` · `rcp_video_apri()` — `fotogramma N SPEDITO: CHIAVE 0x0301 \| delta 0x0302 … B byte di dati` |
| **the rate per second** | from the line `figlio.c`, which the child writes **every second** and which also carries the **empty waits** |
| **the abandons** | `§5.1` `rcp.c` · the withheld keyframe `§5.2` `webtransport.c` ⚠ *(the cited code is no longer there: to be reread)* · `RICHIEDI_CHIAVE … accolta (§5.2)` `rcp.c` · `appunti_posto_libera()` |
| ⭐ **the bytes on the wire** | **they are counted, not deduced**: `/proc/net/dev` on `lo`. `[M]` `lo` **at rest does 0 bytes in 5 s** on this machine (ssh goes through `enp7s0`, the rest is on unix sockets) ⇒ clean counter, and **there is no need to touch `tc`**. ⚠ It is an advantage of the moment, not a law: rest is remeasured at every round |

⛔ **The wire bytes are NOT the frame bytes**: the `SPEDITO` line counts the **payload**,
`lo` also counts QUIC, PCM audio and acks. **Both** are reported, and the difference is
a fact, not an error.

#### ⛔⛔ THE TWO POSITIVE CONTROLS — *and without them the numbers of §3 are not valid*

On a wide line *«abandons 0»* and *«`RICHIEDI_CHIAVE` 0»* have **the same face** as *«the bench
does not look at those counters»* (`LEZIONI.md` §1.9: empty and right look alike). ⇒ Two rounds made
on purpose to make those counters **move**:

| | how | outcome, 23 Aug |
|---|---|---|
| **§5.2** `09-b68-ritmo.py controllo` | the client **requests** a keyframe in the middle of the round | ✅ accepted **1**, passed to the stage **1**, deltas thrown away **1** |
| **§5.1** `09-b68-ritmo.py stretto` | the line narrows to **2 Mbit/s** (`netem` on `lo`, only 7900), only once, then it is restored | ✅ abandons **151**, withheld keyframe **86** |

⛔ **The network is touched with the discipline of `07-b64`/`07-b65`**: only `lo`, only port 7900,
`enp7s0` (ssh + the user's 7730) **never**, a detached guardian that puts the discipline back even if
the script dies. `[M]` verified afterwards: `lo` → `noqueue`, `enp7s0` → `mq`, intact.

### 1.2 ⭐⭐ THE SECOND BENCH — `banchi/09-b71-risveglio.py`, *23 Aug 2026, afternoon*

**The question**: §3.1 measured that with a still scene the rate **stops**, and that the price for whoever
watches is zero *as long as nobody touches anything*. ⇒ ⛔ **how long passes between the first pixel that changes and
the first frame that leaves?**

| | |
|---|---|
| **the shot** | the scene `04-b30-scena` is **frozen** (`SIGSTOP`) and **woken** (`SIGCONT`). ⛔ The process is not switched off and on again: the start of a Wayland client (connection, surface, first buffer) costs tens of ms that **are not the product's wake-up** and would add to the number without anyone noticing |
| ⭐ **the instant of the pixel** | **it is read, not deduced**: `ultimo_disegno_us` in the scene's shared block (CLOCK_MONOTONIC, written at commit, `04-b30-scena.c` · `disegna_una_volta()`). The shot **is not** the moment the pixel changes: in between there is the wake-up of the scene, and it is reported separately |
| **the striker sits on the machine** | `banchi/09-b71-agente.py`, as root: it strikes the shot and catches the first draw by reading `/dev/shm` at ~2 kHz. ⛔ From `ssh` it cannot be done: the network round trip is **a hundred times** the number sought |
| ⭐ **the two clocks are anchored** | the log writes `HH:MM:SS.mmm` **without date and without time zone**. The agent measures the same instant in both ways (epoch + local) and the bench **derives** the offset instead of guessing it. ⛔ If it were wrong the wake-ups would come out negative or hours long: it would be seen, not insinuated |
| **what is measured** | `SPECIFICHE.md` §2.4: the stretch **first pixel → bytes out of the server**. ⚠ **Not** the whole loop — missing are the flight on the wire, decoding and painting on the page, which are phase 8 and **add up, they do not get confused** |
| ⭐⭐ **the comparison** | not a number, a **ladder**: the same wake-up with quiets from 0.2 to 15 s. If the wake-up after 15 s still costs as much as the one after 0.2 s, **the stop costs nothing** |
| **the premise is checked** | during every quiet the bench counts the frames that left: if even one leaves, the desktop **was not still** and the measurement is not what it says it is |

#### ⛔⛔ THE POSITIVE CONTROL — *and it took three attempts, all instructive*

A **known** delay of 200 ms is injected by freezing some processes, and the bench must find it again.

| attempt | where the delay falls | outcome |
|---|---|---|
| I freeze the **child** (capture+encoding) at the shot | ⛔ `colpo → pixel` **0.5 → 191.8 ms** | the delay ends **before** the pixel: it proves nothing about the measured stretch |
| I freeze the **parent** (transport) at the shot | ⛔ `colpo → pixel` **1.1 → 192.0 ms** | **the same**: the stimulus moves together with the instrument |
| ⭐ I freeze the parent **after the pixel has changed** | ✅ wake-up **12.8 → 204.0 ms**, and `colpo → pixel` stays **1.2 ms** | the delay falls **inside** the measured stretch, and the bench sees all of it |

⭐⭐ **And the two failed attempts measured something I was not looking for, and it is not small**:
freezing **any** link of our chain — child *or* parent — stops the **drawing of the
application**. `[M]` 191.8 and 192.0 ms out of 200 injected, with a spread of **0.6 ms**.
⇒ ⛔ **Mutter grants `wl_surface.frame` at the rate of whoever consumes the virtual monitor**: if the
product does not consume, the application inside the session **does not draw**. It is the same line
read from the other end in §3.2 (*«the bottleneck is not the encoder: it is the delivery»*), and it explains
why the 40/s out of 60 requested do not move.

---

## §2 · What was developed

> ⚠ **This line said *«of the product, nothing»* until 09:00 on 23 Aug**, and then it was
> true. During the day **five cures** came in: the list with the switch is in
> **S.3**, the why of each in **§5**, and ⛔ **the seat of the reasoning is the comment in the code**,
> not this document.

### 2.1 In the product — *the five cures of 23 Aug*

| where | what |
|---|---|
| `src/webtransport.c` | ⛔⭐ **the crash cure**: the bytes of a frame are freed at the **ack** (`coda_conferma()`, `:840-870`) or at the closing of the stream, not at serialization. At `:5929` there is the line that killed the server, and the comment names it. ⭐ **the queue threshold** in `video_sgombra()` (`:2705-2800`), with the two counts `sgombra_tenuti` / `sgombra_abbandoni` — so that *«zero abandons»* and *«the cure is off»* do not have the same face |
| `src/codificatore.c` | ⭐ **the quality climb-back** (`risali_qualita()`, `:3446`): counting at delivery, climbing back **at the entry of the next frame**, one rung at a time, with the wait that **doubles** at every relapse. ⭐ **the bandwidth cap** (`:200-340`, `:1786-1800`): `QVBR`, with wire · working point · reservoir **derived from the floor** in one place only |
| `src/pagina.html` | ⭐ **the audio reorder**: `audio_posto_passato()` (`:5882`) computes the **consumption frontier** from `a.base` and `ctx.currentTime`; `a.ist_max_us` (`:5669`) separates *«an overtaken block»* from *«the whole playback late»* — ⛔ without it, a 1 ms overtaking would cost a re-arm, that is **250 ms given away** |
| `src/main.c` · `src/figlio.c` | the **three switches** (`:994`, `:999`, `:1005`), passed to the child in the `argv` (`figlio.c:1162-1165`), and ⭐ **the values in force written at startup in both cases** — on and off |

⭐ And one thing that holds beyond the day: **the parameters line says the VALUES, not the words** —
*«QP 26»*, not *«constant QP»*. The check is §3.12.

### 2.2 In the benches

| | |
|---|---|
| `banchi/09-b68-ritmo.py` | the bench of **invariant I1** — §1.1 above |
| `banchi/09-b68-scena.sh` | starts `04-b30-scena` inside the «prova» session. ⛔ It exists because **a file has no levels of quotes** — see §4 |
| ⭐ `banchi/09-b71-risveglio.py` | the **wake-up** bench — §1.2. It does not rewrite the job: it **imports** `09-b68` for ssh, sudo, `lo`, log, scene and `tc` |
| `banchi/09-b71-agente.py` | the **striker**, runs on the machine: `SIGCONT` and `/dev/shm` at 2 kHz |
| `banchi/09-b71-sessione.sh` | opens a **long, background** session inside the container. ⛔ Same reason as the scene script: four layers of quotes and a redirect towards a root folder |
| `banchi/09-b72-banda.py` | the **bandwidth** bench: the three points at 2560x1080 and the **step** |
| `banchi/09-b72-agente.py` | the **step director**: it changes the `rate` and watches the wire from the machine, because the step lasts 3 s and an `ssh` round costs 0.3 |
| `banchi/09-b72-video.sh` | a **real video** at full screen inside the session. ⛔ It exists because the bands of `--movimento pieno` are **flat colours**: measuring the cost of a video there would give a low and false number |

---

## §3 · The measurements

> All from **23 Aug 2026**, machine 192.168.0.2, port **7900**, user **`prova`**, canvas
> **1920x1080**, codec **HEVC** (`codec 1`), audio **PCM**, **30 s per round**, **wide line**
> (no throttling, `lo`).
> ⚠ **The times are the machine's, which is UTC and two hours behind** the laptop:
> `07:02 UTC` = `09:02 CEST`.

### 3.1 ⛔⭐⭐ I1 — WITH A STILL SCENE THE RATE DOES NOT DROP: **IT STOPS**

> ⚠⚠ **TO BE READ WITH §3.7 BESIDE IT** (written in the afternoon of the same day): these measurements
> were taken with the session in GNOME's **overview**, where a «full
> screen» window is really **a shrunken preview**. ⇒ the shape of the result holds (with a still scene
> zero frames come out, remeasured at 2560x1080), ⛔ **but the bytes of `barra` and `pieno` below
> are those of a fraction of the screen, not of the screen.** The real bytes are in §3.8.

| scene | time | frames/s | KEYFRAME | delta | video payload | bytes on the wire (`lo`) |
|---|---|---|---|---|---|---|
| **still** | 07:02:27 | ⛔ **0.03** | 1 | **0** | 10 147 B · **2.7 kbit/s** | 9 119 569 B · **2.432 Mbit/s** |
| **bar** | 07:03:32 | **39.67** | 1 | 1 189 | 2 171 824 B · **579 kbit/s** | 11 771 322 B · **3.139 Mbit/s** |
| **full** | 07:04:09 | **39.00** | 1 | 1 169 | 10 196 190 B · **2 719 kbit/s** | 20 121 206 B · **5.366 Mbit/s** |
| **still** *(repeated)* | 07:04:44 | ⛔ **0.03** | 1 | **0** | 10 143 B · **2.7 kbit/s** | 9 118 304 B · **2.432 Mbit/s** |

⛔⛔ **With a still scene, in 30 seconds, ONE frame only comes out — the opening keyframe — and then
nothing more.** Repeated twice, **identical**: 1 and 1. It is not a drop: it is a **stop**.

⭐ **And the rate per second says it without averaging it** (`fotogrammi al secondo`, from the child's line):

```
ferma   1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
barra  40 40 40 40 39 41 40 40 40 40 41 40 40 38 39 38 38 40 40 40 41 39 40 40 40 40 40 40 41
pieno  40 39 40 40 38 38 37 38 38 39 37 40 37 40 40 39 40 40 39 39 40 40 39 40 40 41 39 41 40
```

⭐⭐ **AND THE CAUSE IS WRITTEN IN THE LOG BY THE PRODUCT ITSELF**, `figlio.c`, every second:

> *«N frames delivered (K keyframes), **M empty waits (still scene: Mutter delivers only
> when something changes)**»*

| scene | empty waits per second | frames per second | sum |
|---|---|---|---|
| **still** | **123** | 0 | ~123 |
| **bar** | 80 | 40 | ~120 |
| **full** | 81 | 39 | ~120 |

⇒ ⭐ **The child's loop always runs at ~120 Hz**: it does not slow down, it does not save itself, it decides
nothing. What changes is **how many times Mutter puts something in its hand** — 40 out of 120 when the
scene moves, **0 out of 123** when it is still.

⛔ **So the descent is NOT ours, and it is not even a decision**: nobody takes it. The
product **has no rate regulator** (§0.3: bitrate control *does not exist*), and the
source — Mutter's `RecordVirtual` — delivers **only on change**. ⇒ The product's rate
is, today, **the rate at which the compositor deigns to deliver**.

⚠ **What this does NOT say yet**, and it must be said because they are two different questions:
- **the image of whoever watches does not break**: the page keeps the last good frame, and on a
  still desktop the last good frame **is right**. ⇒ ⭐ Literally I1 is violated
  (*«the rate never drops … because the scene is still»*), but **the price for whoever watches is zero
  as long as nobody touches anything**;
- ⛔ **the real price is at WAKE-UP**, and this bench **has not measured it yet**: how long passes
  between the first pixel that changes and the first frame that leaves. It is the measurement that follows.

### 3.2 The rate with a moving scene: **40/s out of 60 requested**

`[M]` The child asks capture for **60/s** (`60/s chiesti`) and receives **39–41**. The cap is not
our encoding: the stretch **capture → bytes out** has a median of **8.12 ms** (bar) and **8.87 ms**
(full) at 1920x1080 — that is ~115/s of capacity. ⇒ ⭐ **The bottleneck is not the encoder: it is the
delivery.** `[?]` To be understood in this phase whether the 40 are a cap of Mutter or of the scene.

### 3.3 The bytes, and ⛔ how much silence costs

> ⚠ **The warning of §3.1 applies**: `barra` and `pieno` were previews, not full screen — §3.7.
> The **still** line instead holds, and is confirmed at 2560x1080 in §3.8.

| scene | video payload | total wire | ⇒ overhead + audio |
|---|---|---|---|
| still | 2.7 kbit/s | 2.432 Mbit/s | ⛔ **99.9 % of the wire is not video** |
| bar | 579 kbit/s | 3.139 Mbit/s | |
| full | 2 719 kbit/s | 5.366 Mbit/s | |

⛔⛔ **With a still desktop the product spends 2.4 Mbit/s to show nothing**: it is the PCM audio
(5 995 blocks × 960 B = 1.53 Mbit/s of payload) plus QUIC. ⭐ It is the observation of v1 R31 turned upside down
(*«the choice is played on how much is spent when it is not needed»*), and this time whoever spends **is not the
video**.

### 3.4 Abandons and keyframe requests — **all at zero, and the reason is good**

| | still | bar | full | ⭐ control at **2 Mbit/s** |
|---|---|---|---|---|
| abandons **§5.1** | 0 | 0 | 0 | **151** |
| withheld keyframe **§5.2** | 0 | 0 | 0 | **86** |
| `RICHIEDI_CHIAVE` accepted | 0 | 0 | 0 | 0 |
| requests **passed to the stage** | 0 | 0 | 0 | **151** |
| deltas thrown away because §5.2 wants a keyframe | 0 | 0 | 0 | **538** |
| audio thrown away / refused | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 3 018** |

⇒ On a wide line **nothing gets queued, so nothing can be abandoned**: the zeros are
the right answer, and the two positive controls of §1.1 prove that those counters **can
move**.

### 3.5 ⛔⭐ AND THE SPIRAL OF §0.3 REPRODUCES AT THE FIRST SQUEEZE — 07:09:38, **2 Mbit/s**, scene `pieno`

| | |
|---|---|
| frames sent | 690 in 30 s = **23.0/s** (against 39.0 on a wide line) |
| of which **KEYFRAME** | ⛔ **152 out of 690** — against **1 out of 1 170** |
| abandons §5.1 | **151** ⇒ ⭐ **one abandon, one keyframe**: the correspondence is almost exact |
| deltas thrown away because a keyframe is needed | **538** ⇒ that is **all** the delivered deltas |
| what reaches whoever watches | **367 frames, 128 keyframes** — out of 690 sent |
| audio | **3 018 datagrams refused by ngtcp2** (on a wide line: 0) |

⇒ ⛔ **It is exactly the spiral that §0.3 had read in the code, here measured on the product of
phase 9**: `video_sgombra()` abandons the delta ⇒ §5.2 opens the debt ⇒ a keyframe leaves ⇒ the keyframe
fills the window ⇒ the next delta does not get out ⇒ it starts again. ⭐ And the stream **degrades in
space AND in time together** (23/s **and** keyframes only) instead of lowering the rate while keeping the deltas,
which is what §8.3 asks.

⚠ **This is a CONTROL, not a measurement of the phase**: 2 Mbit/s is a tenth of the declared
floor (§3.1-bis, 20 Mbit/s). It serves to know that the counters see; the working point must be
measured at 20 Mbit/s and above.

---

### 3.6 ⭐⭐⭐ WAKE-UP **COSTS NOTHING** — *23 Aug, 07:46–08:00 (machine UTC)*

> Port **7900**, user **`prova`**, canvas **1920x1080**, codec HEVC, audio PCM, **wide** line.
> Scene `04-b30-scena --movimento pieno`, frozen (`SIGSTOP`) and woken (`SIGCONT`).
> **180 wake-ups**, 30 for each quiet duration. Bench `banchi/09-b71-risveglio.py` — §1.2.

⛔ **The question**: §3.1 measured that with a still scene the rate **stops**. The price for whoever
watches is zero as long as nobody touches anything — ⛔ **but how much does starting again cost?**

| quiet before the shot | n | **median** | min | max | **p95** |
|---|---|---|---|---|---|
| **0.2 s** | 30 | **13.3 ms** | 12.7 | 13.8 | 13.8 |
| **0.5 s** | 30 | **13.0 ms** | 12.6 | 13.5 | 13.5 |
| **1.0 s** | 30 | **13.6 ms** | 13.0 | 14.3 | 14.2 |
| **2.0 s** | 30 | **13.2 ms** | 12.6 | 13.8 | 13.7 |
| **5.0 s** | 30 | **13.0 ms** | 12.3 | 13.6 | 13.5 |
| **15.0 s** | 30 | **13.2 ms** | 12.6 | 13.8 | 13.8 |

⭐⭐ **The answer is flat: waking from still costs NOTHING.** Between 0.2 s of quiet and 15 s
of quiet the difference is **0.3 ms out of 13** — inside the noise. ⛔ And it is not a median that hides
a tail: **all 180 measurements lie between 12.3 and 14.3 ms**, that is the tail is **2 ms** wide.
`LEZIONI.md` §6.5 asks for the tail because *«the regime is blind to the tail»*: here the tail was
looked at and **it is not there**.

⇒ ⭐ **The stop with a still scene is not a defect of the phase.** The rate stops because Mutter does not
deliver, and it restarts at the first pixel as if it had never stopped.

**What is measured** (`SPECIFICHE.md` §2.4): **first pixel → bytes out of the server**.
⚠ **Not** the whole loop: missing are the flight on the wire, decoding and painting, which belong to
phase 8 and **add up**. ⭐ The *scene*'s stretch is declared separately and is worth **0.3–0.4 ms**
(the `SIGCONT` and the drawing): it is not ours and it is not inside the 13.

⭐ **And where those 13 milliseconds go** — from the per-frame lines of the log:

| | median |
|---|---|
| pixel → start of encoding (**Mutter composes and delivers to us, plus our capture**) | **10.2–10.9 ms** |
| **encoding**, which is ours | **2.6–2.7 ms** |
| end of encoding → `SPEDITO` (delivery to the transport) | **0.0 ms** (below the log's millisecond) |

⇒ ⛔ **80 % of the wake-up is waiting for the compositor, not our work**, and it is consistent with a
60 Hz virtual monitor (average half period = 8.3 ms). ⭐ **There is nothing to optimize in
here**: the part we can touch is 2.7 ms out of 13.

**The first frame that leaves is always a `delta`** (180 out of 180), median **2.9–3.1 KB**: the
wake-up **does not cost a keyframe**.

### 3.7 ⛔⭐⭐ AND THIS MORNING'S BENCH WAS MEASURING AN OVERVIEW — *08:08*

`[M]` **Looked at in the capture's pixels**: the headless GNOME session sits in the **overview**
(the *Activities* Overview) and stays there, because nobody ever pressed a key inside.
⇒ the windows are not windows, they are **shrunken previews** in the middle of the screen, with the
bar at the top and the drawer at the bottom.

⛔⛔ **So «full screen» in this morning's benches was not full screen**, and the numbers of
§3.1–§3.3 are those of **a fraction of the screen**. The shape of the result of §3.1 does not change
(with a still scene zero frames come out: remeasured at 2560x1080, **0 in 30 s**), ⚠ **but the bytes do**.

⭐ **The cure, and it is not a trick**: an **ESC** is sent through the door the product itself uses —
`org.gnome.Mutter.RemoteDesktop` (`banchi/09-b72-tasto.py`). That is, one does **what happens when
the user presses a key**. The two more comfortable routes are closed and I tried them:
`org.gnome.Shell.Eval` → `(false, '')`; `org.gnome.Shell.FocusApp` → `AccessDenied`.

### 3.8 ⭐⭐⭐ BANDWIDTH AT 2560x1080 — **full-screen video asks for 293 % of the floor**

> User **`prova2`** (new stage), canvas **2560x1080**, 30 s per point (25 s for the grain),
> **wide** line, `08:22–08:35`. Bench `banchi/09-b72-banda.py`. ⭐ Every scene was
> **looked at in the pixels** before being believed.

| scene | fps | keyframes | **video payload** | **% of 20 Mbit/s** | wire `lo` |
|---|---|---|---|---|---|
| **still** (nothing) | **0.00** | 0 | **0** | **0 %** | 2.426 Mbit/s |
| **video: the user's real desktop, full screen** | 23.10 | 0 | **0.204 Mbit/s** | **1.0 %** | 2.678 |
| **full**: flat-colour bands, the whole screen | 40.57 | 0 | **1.179 Mbit/s** | 5.9 % | 3.730 |
| **bar**: **halftone** gradient over the whole screen + bar | 34.93 | 1 | **21.356 Mbit/s** | ⛔ **106.8 %** | 24.219 |
| ⛔ **video with grain, full screen** | 23.44 | 0 | ⛔ **58.668 Mbit/s** | ⛔ **293.3 %** | **61.671** |

⛔⛔ **The answer to the question of §0.3 is yes: a bitrate control is needed.** With **fixed QP 26**
and **no cap**, hard content at full screen asks for **three times the declared floor**
— 312 861 bytes per frame on average, 23 per second. ⚠ And this morning's `[?]` (**~19.9
Mbit/s**, rescaled from v1) was **optimistic by three times**.

⭐⭐ **And the three points together say what a single number would not say**: bandwidth does not depend
on the *surface* that moves, it depends on the **content**. `pieno` moves **all** the pixels and costs
**1.2 Mbit/s**; `barra` moves the same pixels with a **halftone** and costs **21**; the film with
grain costs **59**. ⇒ ⛔ **«how many pixels change» predicts nothing**, and a regulator built
on that quantity would be wrong by two orders of magnitude.

⭐ **The user's real desktop, full screen and moving, costs 1 % of the floor**
(0.204 Mbit/s). ⇒ On the content the product exists for, today **there is no bandwidth
problem**: the problem is the hard case, and it is for the hard case that the cap must be written.

⚠ **The clip and the player are declared**, because another player would give another rate:
`scena-utente.webm` (2560x1080, VP8, 17.5 s, 404 frames at ~23/s — **the same file** on which
phase 8 measured 24 956 bytes per keyframe), played by **firefox-esr** at full screen.
⛔ On the machine there are no mpv, ffplay, gst-launch, totem, vlc nor ffmpeg: Firefox is **the only
player**, and it is also the user's real one.

### 3.9 ⛔⛔ THE PRODUCT DIED OF SEGV ON THE 525 KB FRAME — *08:28:09*

`[M]` `journalctl -u remotix-7900.service`:
> `Main process exited, code=killed, status=11/SEGV`

⭐ **The last line of its log, in the same second**:
> `08:28:09.894 figlio  codec 1: 525298 byte, delta, caricamento 0 us, codifica 2597 us`
> `08:28:09.895 rcp     fotogramma 185 SPEDITO: delta 0x0302, codec 1, 2560x1080, 525298 byte…`

It was the first frame of the **film with grain**. ⚠ **Not reproduced**: the next round, with the
same clip, held for 25 seconds and 586 frames (median 313 KB, peaks over 500 KB).
⛔ No `core` (coredump disabled) and no OOM in `dmesg`: the unit's peak memory
was **41.2 MiB**.

> ⭐⭐⭐ **And in the afternoon the cause was found, line by line: §4.** This box stays
> as it was written in the morning — *«`[?]` the cause is not named»* — because it is the record of what
> was known at 08:28, and §4 is what was learned afterwards. ⭐ And the sentence *«it did not repeat»*, which
> then seemed a mitigating circumstance, became **the proof**: §4.4 explains **why** the next round could
> not die.

### 3.10 ⭐⭐⭐ THE STEP — **a 3-second hole is enough, and the return is immediate**

> Scene **`barra`** (the one asking for 21 Mbit/s: below the 10 of the hole there is a **real deficit**),
> canvas 2560x1080. `netem` on `lo`, only port 7900, `delay 15ms` **in all three phases** —
> only the `rate` changes, so the transient is of bandwidth and not of RTT. `08:32`.
> ⭐ The change of discipline costs **4.0–4.7 ms**, measured: on a 3 s hole it is 0.15 %.

| s | fps | **keyframes** | delta | abandons §5.1 | wire Mbit/s | phase |
|---|---|---|---|---|---|---|
| 5 | 32 | 3 | 29 | 3 | 22.1 | wide |
| 6 | 38 | 1 | 37 | 1 | 26.3 | wide |
| 7 | **40** | **0** | 40 | **0** | 28.2 | wide |
| **8** | ⛔ **14** | ⛔ **6** | 8 | **7** | **8.5** | **narrow** |
| **9** | ⛔ **14** | ⛔ **7** | 7 | **6** | **8.3** | **narrow** |
| **10** | ⛔ **13** | ⛔ **7** | 6 | **7** | **8.0** | **narrow** |
| 11 | 32 | 2 | 30 | 2 | 24.1 | *the line reopens at +11.1 s* |
| **12** | ⭐ **42** | ⭐ **0** | 42 | **0** | **29.2** | wide |
| 13…28 | 39–41 | **0** | | **0** | 27.6–29.0 | wide |

⛔⛔ **Yes: a hole is enough.** A sustained poor line is not needed — **three seconds** bring the rate
from 40 to 13/s and turn **half the frames into keyframes** (7 out of 13). It is the spiral of
§0.3, identical to the one seen at constant 2 Mbit/s, triggered by a transient.

⭐⭐ **And the correspondence is exact, at every level**: `abbandoni §5.1` = `chiavi`, one to one —
7↔6, 6↔7, 7↔7 in the hole, and also **on the wide line** (3↔3, 1↔1). ⇒ ⛔ It is not «the poor line makes
keyframes come out»: it is **`video_sgombra()` abandoning a delta, and every abandon buys a keyframe**.
The poor line only increases the abandons.

⭐⭐⭐ **But the return is immediate, and this is the good news**: the line reopens at +11.1 s, the
11th second is a transition (32 frames, 2 keyframes) and **the 12th second is already full regime** — 42
frames, **zero keyframes**, 29.2 Mbit/s. ⇒ **less than a second**, and no aftermath in the following 17
seconds. ⛔ **There is no hysteresis**: the product has no regulator that «remembers» having
gone down, so it has nothing to bring back up either.

#### ⛔ THE CONTROL, and without it the step proves nothing

Same step, scene **`pieno`** (3.7 Mbit/s on the wire, that is **below** the hole):

| s | 8 | 9 | 10 | 11 |
|---|---|---|---|---|
| fps | 40 | 39 | 39 | 40 |
| keyframes | **0** | **0** | **0** | **0** |
| abandons | **0** | **0** | **0** | **0** |

⇒ ⭐ When the requested bandwidth is below the hole **absolutely nothing happens**. The bench does not
fire blanks: it fires when there is a deficit, and only then. ⛔ And this also says the other half:
**throttling at a constant 20 Mbit/s would have shown nothing**, exactly as predicted.

---

## §3-bis · ⭐⭐ THE PAIRED COMPARISON — *the three cures of 23 Aug, measured*

> ⛔ **The question, only one**: are the three cures applied this morning **in force**, and did the
> behaviour change **where it had to and only there**?
>
> ⚠ **The times are the machine's, which is UTC** and two hours behind the laptop.
>
> ⛔⛔ **And «the three cures» of this chapter are NOT «the five cures» of S.3** — it is a collision of
> names, and it must be untangled here or in an hour nobody will untangle it any more. The three of this morning are:
> **cure 1** = the **audio reorder** in `pagina.html` (= **cure 4** of S.3, §5.4) ·
> **cure 2** = the encoder line that says **the values** (*«QP 26»*, not *«constant QP»*) ·
> **cure 3** = the **declarations** of the level and of the parameters in force. ⇒ Cures 2 and 3 are the
> *«sixth thing»* of S.3: they do not change a pixel, they change what the log can say.
> ⚠ The other four of S.3 — the crash, the queue threshold, the climb-back, the bandwidth cap —
> were written **after** these measurements, and **were not measured here**.

### 3.11 ⭐ THE «AFTER» EXISTS, AND THE «BEFORE» STAYED ALIVE — *08:45 – 08:48*

| | |
|---|---|
| the **after** tree | `/media/REMOTIX/src/09b-src` — ⛔ **not** `09-src`, which is the one running on 7900: if the build had failed we would have gone back without rebuilding anything |
| the build | `enter.sh --root 'bash /srv/src/09b-src/src/costruisci.sh'`, **08:47** · `make` exited **0** · binary `/media/REMOTIX/src/09b-src/src/remotix` |
| ⛔ the two copies of `rcp.c` | `md5 eed49ac7bf007796f051e5db5bb425c7` — **identical**, `src/` and `banchi/rcp/`, or the Makefile refuses |
| the after server | port **7910**, unit `remotix-7910.service`, work `/media/REMOTIX/tmp/09b`, started **08:47:46** |
| ⭐ the tool is in the repository | `banchi/09-riavvia-7910.sh` — *«a tool outside the repository is a tool nobody rereads»* |
| A6 verified | `⭐ VERIFICATO: il server e' fuori da ogni sessione utente (0::/system.slice/remotix-7910.service)` |
| the **before** | 7900 **alive and intact**, this morning's binary, tree `09-src` — it is the term of comparison |

⛔⛔ **AND THE «AFTER» IS A SNAPSHOT OF 08:45, not «the code of now»** — it must be written here or in
an hour nobody will know any more what was measured. On 7910 runs **exactly** this:

| file | `md5` of what runs on 7910 |
|---|---|
| `src/codificatore.c` | `a35938a8c1fe8f22c4d9bf4c064bc13e` |
| `src/codificatore.h` | `bfb22009e166c23556e1a302f32b2395` |
| `src/figlio.c` | `f300a36ca2b07bfdffe1e72867b5edfd` |
| `src/pagina.html` | `e010d615f10643d5c6e2a2c01ae5ff25` |
| `src/rcp.c` = `banchi/rcp/rcp.c` | `eed49ac7bf007796f051e5db5bb425c7` |

⚠ In the afternoon others kept working on the repository: at 09:55 `codificatore.c`,
`codificatore.h`, `figlio.c`, `webtransport.c`, `main.c` and `figlio.h` **no longer match**
this snapshot (`pagina.html` and `rcp.c` do). ⇒ ⛔ **These numbers hold for the three cures as
they were at 08:45, and for nothing else**: whoever wants to judge the afternoon's work must
rebuild and remeasure.

⚠ **And the benches took port, tree and folder from the environment** (`LAV`, `DENTRO_ALB`,
`DENTRO_LAV`, `ALB_NOME`, `PORTE_AMMESSE`), with the **defaults unchanged**: every round of this morning
redoes itself identically without writing anything. ⛔ And `pulizia()` now **declares** the ports it tolerates
instead of demanding only one: two servers running are not dirt, measuring in two is.

### 3.12 ⛔⭐⭐ THE THREE CURES ARE IN FORCE — the lines, **verbatim** — *08:51:26 – 08:51:29*

⛔ It is lesson **E1**, *«written is not in force»*: the lines are reported as they came out, and
beside them there is the **control** — the same session on 7900 does not have them.

**Cure 2 — the encoder** (`08:51:29.083`, channel `video`):

> `aperto: HEVC 8 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD driver … ⚠ EncSliceLP, bassa potenza — NON e' la codifica piena) · 1920x1080 · **QP 26 costante** · chiavi solo su richiesta`
>
> `la scala della degradazione, coi valori in vigore: **QP 26 → QP 35 → QP 44 → QP 51** — passo 9 (CRF_PASSO), fondo 51, uscita dal senza-perdita a CRF 24 (CRF_DI_EMERGENZA), e un DELTA si abbandona dopo 3 ricodifiche (RICODIFICHE_MASSIME).  ⚠ Una CHIAVE non si abbandona mai (RCP.md §5.2): per lei la scala si percorre fino in fondo`
>
> `la risalita della qualita' e' **SPENTA** (invariante I6): scesa una volta, la qualita' resta giu' per tutta la sessione — e questa riga e' il perche', non «non ha mai dovuto scattare».  ⚠ Si accende con \`codificatore_qualita_risale(true)\`, e da spenta questi numeri (**120 fotogrammi, 2097152 byte, scalino 9, punto di lavoro QP 26 costante, tetto d'attesa 3840**) non hanno nessun effetto`

⭐ **The parameters line says the VALUES, not the words**: «QP 26», not «constant QP». ⛔ The
control: the same line on **7900** says `… · 2560x1080 · **QP costante** · chiavi solo su
richiesta` — the number is not there.

**Cure 3 — the declarations** (`08:51:26.861` `rcp`, `08:51:26.961` and `08:51:29.097` `figlio`):

> `il client dichiara video.livello=5.1 (= 5.1, cioe' level_idc 51 in H.264 e L153 in HEVC): §4.3 vieta al server di emettere un flusso PIU' ALTO di questo`
>
> `⚠ e il livello PRODOTTO non si legge da qui: sta nella riga «PRIMO fotogramma codificato» del figlio, campo «livello» (§4.3 riga 701) — il confronto lo fa chi legge il registro, il programma NON lo fa ancora`
>
> `⭐⛔ PARAMETRI IN VIGORE (fase 9), quel che il figlio CHIEDE: cadenza **60/s** · tela alla nascita **1920x1080** · GOP INFINITO (chiavi_ogni = 0: chiavi solo a richiesta, §5.2 — e' una scelta, non una dimenticanza)`
>
> `⭐⛔ PARAMETRI IN VIGORE (fase 9), qualita' e codificatore CHIESTI: **QP 26** in hardware · **CRF 20** sul ripiego in software (due grandezze diverse, non si confrontano) · nodo **/dev/dri/renderD128** · entrypoint **EncSliceLP (bassa potenza)**`
>
> `⭐⛔ §4.3 — LIVELLO PRODOTTO: **4.0** (nell'SPS e' 120, cioe' general_level_idc, che e' il triplo) · stringa per il decodificatore «hev1.1.6.L120.B0».  ⛔ §4.3 vieta di superare il \`video.livello\` del client: il numero CHIESTO sta nella riga «il client dichiara video.livello=…» di \`rcp\`, e il confronto fra le due righe lo fa CHI LEGGE — il programma NON lo fa`

⭐⭐ **And the comparison, made by whoever reads, gives green at the first shot**: the client asks for **5.1**,
the server produces **4.0** ⇒ §4.3 is respected. ⛔ Until this morning that comparison **could not
be made from outside**: one of the two numbers was not written anywhere.

**The control — 7900 has none of these lines.** `grep -c` on its log:

| line | 7910 (after) | 7900 (before) |
|---|---|---|
| `PARAMETRI IN VIGORE` | 2 | **0** |
| `la scala della degradazione` | 1 | **0** |
| `risalita della qualita` | 1 | **0** |
| `LIVELLO PRODOTTO` | 1 | **0** |
| `il client dichiara video.livello` | 1 | **0** |

**Cure 1 — the audio counters** (read **on the served page**, not in the source):

| | 7910 (after) | 7900 (before) |
|---|---|---|
| `audio_posto_passato` (the computed frontier) | **2** occurrences | **0** |
| `" tardivi " + c.scartati_tardivi` on the status line | **1** | **0** |

⇒ ⭐ The cured page **is the one the after server delivers**: `curl https://192.168.0.2:7910/`
carries it, `…:7900/` does not. ⚠ The page is read **once at startup** (`pagina.c` · `pagina_muovi()`) — this is
the check that that restart was needed.

### 3.13 ⭐⭐⭐ THE WAKE-UP: **identical** — *7900 at 09:07–09:09, 7910 at 09:18–09:20*

> Same scene (`04-b30-scena --movimento pieno`), same user `prova`, canvas 1920x1080,
> **30 shots per point**, wide line. ⛔ **One at a time**: between the two rounds the machine was
> reset to zero (no live stage, no discipline).

| quiet | **7900 · median** | p95 | first frame | **7910 · median** | p95 | first frame |
|---|---|---|---|---|---|---|
| **0.2 s** | **12.4 ms** | 12.9 | 2 988 B | **12.0 ms** | 12.5 | 2 981 B |
| **2.0 s** | **11.9 ms** | 12.4 | 2 880 B | **12.4 ms** | 13.2 | 2 889 B |
| **15.0 s** | **12.1 ms** | 12.7 | 2 928 B | **12.7 ms** | 13.2 | 2 878 B |

⭐⭐ **Identical**: the difference between the two servers is **0.4–0.6 ms out of 12**, that is less than the
difference between two quiets of the same server. ⛔ And it is not a median that hides a tail: the
p95 lie between 12.4 and 13.2 on all six points. ⭐ The **first frame** is `delta` 180 times
out of 180 and weighs **2 878 – 2 988 bytes**: the two servers differ by **less than 0.5 %**.

⚠ And this morning's 13 ms (§3.6) became 12: the machine is the same, the session is new.
⛔ **That is why the «before» was remeasured now instead of believing the number of 07:46** —
a paired comparison is made with two close measurements, not with one from three hours ago.

**Where they go**: pixel→encoding **9.2–9.9 ms** · encoding **2.5–2.6 ms** · encoding→`SPEDITO`
**0.0 ms**, on both servers in the same way.

### 3.14 ⭐⭐ I1 — WITH A STILL SCENE, **identical** — *7910 at 09:31–09:33, 7900 at 09:35–09:38*

> Bench `09-b68-ritmo.py tutto --secondi 30`, user `prova`, canvas 1920x1080, wide line.

| scene | **7900** fps | K + Δ | video payload | wire `lo` | **7910** fps | K + Δ | video payload | wire `lo` |
|---|---|---|---|---|---|---|---|---|
| **still** | **0.07** | 1 + 1 | 5 559 B · 1.5 kbit/s | **2.429** Mbit/s | **0.07** | 1 + 1 | 5 565 B · 1.5 kbit/s | **2.431** Mbit/s |
| **bar** | 37.03 | 1 + 1 110 | 62 036 040 B · 16 543 kbit/s | 19.925 | 34.60 | 1 + 1 037 | 58 005 654 B · 15 468 kbit/s | 18.790 |
| **full** | 39.97 | 1 + 1 198 | 4 936 055 B · 1 316 kbit/s | 3.920 | 40.17 | 1 + 1 204 | 5 038 472 B · 1 344 kbit/s | 3.947 |
| **still** *(repeated)* | **0.07** | 1 + 1 | 5 556 B | 2.431 | **0.07** | 1 + 1 | 5 551 B | 2.431 |
| abandons §5.1 · withheld keyframe §5.2 | **0 · 0** | | | | **0 · 0** | | | |
| the client's `vecchi` audio | **0** | | | | **0** | | | |

⭐⭐ **The measurement that counts is the cost PER FRAME, not the count of frames**: on `barra`
it is **55 838** bytes (7900) against **55 882** (7910), that is **0.08 % of difference**. ⇒ The
encoder does the same thing; what wobbles by 6 % is **how many times Mutter delivers**, which is the
same quantity as §3.1 and is not ours.

⛔ **And audio on the local path confirms the premise of cure 1**: `vecchi` **0** on
both, in all four rounds. There was nothing to cure, and indeed nothing changed.

⚠ `barra` here costs **16–20 Mbit/s** against the 579 kbit/s of §3.1: those were previews of the
overview (§3.7), these are not. ⛔ The comparison that holds is **column against column**, not
against this morning.

### 3.15 ⭐⭐⭐ BANDWIDTH AT 2560x1080: **identical to the byte** — *7910 at 09:44 and 09:51, 7900 at 09:47*

> Bench `09-b72-banda.py punti`, user **`prova2`**, canvas **2560x1080**, **25 s** per point,
> wide line. The «video» point is the **user's real desktop**: `scena-utente.webm` at full
> screen in `firefox-esr`, that is the content the product exists for.

| point | **7900** fps | **video payload** | % of 20 Mbit/s | B/frame | wire `lo` | **7910** fps | **video payload** | % | B/frame | wire |
|---|---|---|---|---|---|---|---|---|---|---|
| **still** | 0.00 | **0** | 0 % | — | 2.427 | 0.04 | **632 B** | 0 % | 632 | 2.427 |
| **full** | 41.00 | **1.159 Mbit/s** | 5.8 % | 3 532 | 3.683 | 41.28 | **1.159 Mbit/s** | 5.8 % | 3 508 | 3.687 |
| **video** *(real desktop)* | 21.96 | **0.193 Mbit/s** | **1.0 %** | 1 099 | 2.666 | 21.92 | **0.195 Mbit/s** | **1.0 %** | 1 112 | 2.667 |

⭐⭐⭐ **`pieno`: 3 620 466 bytes against 3 620 630, over 25 seconds and ~1 030 frames.** That is
**164 bytes of difference out of 3.62 MB — 0.005 %.** ⛔ Not «similar»: the same encoder that
does the same thing.

⭐ **And the real desktop costs 1.0 % of the floor on both** — 0.193 against 0.195 Mbit/s,
that is the number of §3.8 (0.204) found again twice four minutes apart.

⚠ The `pieno` point on 7910 was **redone at 09:51**: at the first round the scene had not
started — `⛔ shm_open(//09-b68): Permission denied`, the shared memory segment had remained
`prova`'s (uid 1001) from the I1 bench and `prova2` (1002) could not open it. ⛔ **A bench
defect**, not a product one: `09-b68-scena.sh` does not clean `/dev/shm/09-b68` between two different
users, and the symptom is «the scene does not start», which is mute about the why.

### 3.16 ⛔⛔ AUDIO UNDER `netem` — **and here I stop: the prescribed bench CANNOT see cure 1**

> `banchi/07-b64-rete.py netem --solo 2-jitter --secondi 25` — `netem delay 20ms 2ms` on `lo`,
> **only the measured port**, `enp7s0` never touched, guardian armed. One at a time:
> 7900 at **09:41**, 7910 at **09:45**.

| | **7900 · the BEFORE** | **7910 · the AFTER** |
|---|---|---|
| sent by the server | 5 005 | 5 005 |
| received | 3 966 | 4 006 |
| **`vecchi` (discarded §6.3)** | **1 024** | **980** |
| **purity** | **0.1149** | **0.1235** |
| sample yield | 0.79495 | 0.80281 |
| instant holes · crackles/s | 938 · 42.31 | 917 · 41.24 |

⛔⛔ **The prediction was «0.175 → ≥ 0.95». It came out 0.1149 → 0.1235, that is NOTHING. And the number
does not refute the cure: it refutes the bench.**

⭐ **The reason, and it is read in the bench's code, not in the product.** Whoever discards the overtaken
datagrams in this round **is not `pagina.html`**: it is the test client, `banchi/01-b3-cliente.py`
line **743**, which has **its own** copy of the rule of §6.3 —

```python
if self.a_ultimo_istante is not None and istante <= self.a_ultimo_istante:
    self.a_vecchi += 1
    return
self.a_ultimo_istante = istante
```

— that is **exactly the old line**, the one that compares with the **last arrived**. The cure was
written in `src/pagina.html`, which in this bench **never runs**. ⇒ `vecchi` and `purezza`
here **must** be equal on the two servers, and they are.

⭐⭐ **And the proof that it is so, not the argument**: `md5sum` of `01-b3-cliente.py` in the two trees —
`13e68d19ed44298b7926cded53affdda` in `09-src` **and** in `09b-src`. **The same file, byte for
byte.** A bench that measures itself can only give the same number.

⛔ **So I stop on this cure, and I say why**: `07-b64-rete.py` is a **transport** bench
— it measures how many datagrams pass the wire and how pure the tone that comes out is — and cure 1 lives
in the **real client**, that is in the page. The two halves do not touch.

**What WAS verified of cure 1**, and what **was not**:

| | |
|---|---|
| ✅ the cured page is **delivered** by 7910 and not by 7900 | §3.12, read with `curl` on the port |
| ✅ the four new counters (`tardivi`, `fuori`, `rec`, `dop`) are **on the status line** and **come out of `audio_conti()`** towards `/diario` | read in the served page |
| ✅ on the **local path** the `vecchi` are **0**, as predicted ⇒ there was nothing to loosen | §3.14 |
| ⛔ **NOT verified**: that under real reordering purity rises to ≥ 0.95 | a bench is needed that runs **the page**, not the test client |

⭐ **What shape that bench would have**, so that next time we do not start from scratch: a
**real browser** that opens `https://192.168.0.2:PORTA`, logs in as `prova`, and whose counters are
read **without asking the user anything** — the page already sends them on its own to the server every 5 s
(`pagina.html` · `avvia_audio()`, `fetch("/diario?" + riga)`), and the line carries all four new numbers.
⇒ The server's log becomes the record. ⛔ **The missing piece is where to run the
browser**: on the machine Firefox 140 ESR is there, but it lives **only inside a REMOTIX session**
(there is no `Xvfb`), and pointing it at the server that is capturing it is a mirror; and the `netem` must
stay on `lo`, because **`enp7s0` is never throttled**. ⚠ It is a bench choice, and it must be made
before writing it — not after.

### 3.17 ⛔⛔ TWO FALSE ALARMS OF THE BENCH, AND THEY ARE WORTH MORE THAN A NUMBER

**1. «The after is slower and its frames weigh double» — *08:52, and it was not true*.**
The first wake-up round on 7910 gave a median of **13.4 / 14.0 / 13.8 ms** against the
**12.4 / 11.9 / 12.1** of 7900, and a first frame of **6 141 / 5 872 / 5 812 bytes** against
**2 988 / 2 880 / 2 928**: **double**, systematic over 90 shots, with the same scene.

⛔ The cause was not the product: it was **an orphan stage from this morning** — `prova2`'s child
left alive on 7900 after the bandwidth bench of 08:30 (invariant I4: the stage survives
the detach) — which kept capturing and encoding on the **same integrated GPU**. With that one closed
and the measurement redone on the clean machine, the after gave **12.0 / 12.4 / 12.7** and a first
frame of **2 981 / 2 889 / 2 878**: identical to the before.

⇒ ⭐⭐ It is `LEZIONI.md` §1.26 caught red-handed: **it did not give a red, it gave a plausible
number** — and that number, believed, would have accused three innocent cures. ⚠ And the line that
denounced it was printed by the bench itself and I had not weighed it: *«frames that left DURING the
quiets: **1 · 1 · 7**»* against *«0 · 0 · 0 (the desktop was really still)»* of the clean round.

**2. «The after sends almost nothing» — *09:29, and it was not true*.**
The first I1 round on 7910 gave `barra` at **0.17 fps** and **13 kB** on the wire in 30 s. In the
log the cause, verbatim:

> `09:29:05.841 rcp     posto NEGATO a prova da [192.168.0.2]:55729: lo occupa un altro client di questo stesso utente (occupati: 1)`
>
> `09:29:12.006 rcp     STACCATO per silenzio: 30002 ms senza un PACCHETTO da [192.168.0.2]:33357 — e l'ultimo byte di RCP e' di 657637 ms fa`

⇒ The previous bench's client had been **killed** instead of dismissed, and the server kept
its place until the **30 seconds of silence** of §5.3 — that is for the whole first round. It is the same
defect already written in `banchi/09-b71-sessione.sh` (`[M]` 23 Aug 08:06), which there is cured by sending
`TERM` and waiting; ⛔ **but between one bench and the next the wait is not there**, and nobody does it.

⚠ **Operating rule that comes out of it**: between two benches on the same user one **verifies that the place
is free** (no `01-b3-cliente.py` alive **and** no stage), one does not count the time.

---

## §4 · ⛔⛔⛔ THE CRASH OF 08:28:09 — the cause, proven line by line

> **Diagnosis of 23 Aug 2026, afternoon.** ⭐ The cure was **applied the same day**
> (§5.1). ⚠ What follows is the *cause*, not the story of the hunt.

### 4.1 ⭐⭐⭐ The cause, in one line

`src/webtransport.c` (tree `09-src`, the one that ran) **freed** the bytes of a frame
as soon as ngtcp2 had *serialized* them. The contract of `ngtcp2_conn_writev_stream()`
(`/media/REMOTIX/src/b2/ngtcp2/lib/includes/ngtcp2/ngtcp2.h:5246-5250`) says the opposite:

> *«The caller must keep the portion of data covered by `*pdatalen` bytes **in tact** until
> `ngtcp2_callbacks.acked_stream_data_offset` indicates that they are acknowledged by a remote
> endpoint or the stream is closed.»*

⇒ **Use after free.** `ndatalen` says how many bytes ended up **in a packet**, not
how many are **acknowledged**. The ack callback **existed** (`trasporto.c` · `accetta()`) but it only forwarded to
nghttp3: nobody consulted it before the `free`.

⭐⭐ **And the defect was there on EVERY retransmitted frame, always.** The 525 298-byte one was
only the first **large** enough to make it noisy.

### 4.2 The proof that remained on the machine — ⭐ `dmesg` saved the day

⛔ No core: `coredumpctl` is not installed and `core_pattern` is `core` (relative name) in the
service's working folder (`/`), where it is not. ⭐ But `dmesg -T`:

```
[Sun Aug 23 08:28:10 2026] remotix[14739]: segfault at 7f148e056fc2 ip 00007f1495a88b49
    sp 00007ffc182131f8 error 4 in libc.so.6[162b49,7f149594e000+163000]
```

| piece | what it says |
|---|---|
| `error 4` | **read** in user space of a page **not present** — not a write, not a permission |
| `segfault at 0x7f148e05…` | **`mmap`** zone: it is not the stack (`sp` is `0x7ffc…`), it is not the `brk` heap of a PIE (`0x55…`) |
| `ip` at **offset 0x162B49** in libc | `objdump`: `vmovdqu (%rsi),%ymm0` inside `__memmove_avx_unaligned_erms` — the **very first 32-byte read from the SOURCE** |

⇒ `%rsi = 0x7f148e056fc2` **is not garbage** (not `NULL`, not `0xdead…`): it is a **plausible**
pointer into a region **no longer mapped**. ⭐ **It is the exact signature of a use after
free of an `mmap` block.**

⭐ The log confirms the sequence: the frame **had been copied successfully**
(`coda_metti()` copies the bytes before `SPEDITO` comes out), between `.895` and the death (`.9237`) pass
**~28 ms** and **nothing happens other than writing to QUIC** — no frame 186, no
re-encoding, no scene change. And the jump is **146 → 525 298 bytes**, ×3 600 in one frame.

### 4.3 ⛔ The six suspects, each closed with its own line

| suspect | the line that decides |
|---|---|
| **16 MiB** cap / **re-encoding** loop | 525 298 bytes is **3.1 %** of 16 MiB, and *«si RICODIFICA»* appears **0 times** in the dead round |
| `abbassa_qualita()` / `chiudi_contesto()` with a packet in hand | it is called **only** from the cap branch, **never taken**. ⚠ `fuori->dati = c->pacchetto->data` remains a **real defect in waiting** — but it is not the one of 23 Aug |
| **output queue** `WT_CODA_MAX` (17 MiB) | 525 KB fit with room to spare; *«NON entrano in coda»* and *«la coda ha toccato il tetto»*: **0 times** |
| `video_sgombra()` / `WT_INVOLO_MAX` | ⭐ **and it is excluded for the good reason**: it does `shutdown_stream_write()` **before** throwing away the bytes, and it is **correct**. ⛔ Its comment — *«FIRST the stream is reset, THEN the bytes are thrown away»* — proves that **the rule was known**, and makes it sharper that the other spot did not have that protection. Moreover it was not even called: no frame arrived after 185 |
| **zero copy** (phase 8), stride a multiple of 64 | 2560 px → stride 10 240 = 64 × 160 ✔; and anyway it is the **input** route, already finished well at `.894` |
| the frames' **pool** | it is the one of the **VAAPI surfaces**, of fixed size and opened once with the context |

### 4.4 ⭐⭐⭐ Why **that** frame and not the other 45 004 — and why the next round did not die

The queue allocation doubles from 64: for 525 298 bytes the capacity rises to **1 MiB**. Above
**128 KiB** (the default `M_MMAP_THRESHOLD`) glibc serves with `mmap`, and `free()` does `munmap`: **the
region disappears**. Below, the block stays in the heap and the wrong read **reads garbage
without making noise**.

| capacity class, in the dead round | how many |
|---|---|
| **> 512 KiB** ⇒ capacity 1 MiB, `mmap` | **1** ← frame 185 |
| > 128 KiB | 0 |
| ≤ 128 KiB (heap, **silent**) | **45 004** |

⇒ **The only `free()` that really unmapped a region in 1 h 50 min**, hence the only time
the dangling pointer of ngtcp2 found an absent page instead of recycled heap.
⭐ And the second multiplier: 525 298 bytes are **~370 packets** in a burst — that at least one is
declared lost (or that a PTO probe fires) in the following 28 ms is **almost certain**. With a
146-byte delta the packet is **one**.

⭐⭐ **And the next round — 586 frames, peaks over 500 KB — did not die for the same reason
read backwards: glibc's `mmap` threshold is dynamic.** When freeing an `mmap` block,
`munmap_chunk()` **raises** `mp_.mmap_threshold` to the size of that block. ⇒ After the **first**
1 MiB buffer freed, the following ones come from the heap and the use after free goes back to being
**silent**: garbage bytes on the wire instead of a `SEGV`.

⇒ ⛔ **It is not the size alone.** It is: *the first time a large block is freed while
ngtcp2 still holds it for retransmission.*

### 4.5 ⏳ How to reproduce it — ⛔ **not run**, and the prediction is falsifiable

| recipe | how | **prediction** |
|---|---|---|
| ⭐ **A** — deterministic, without network and without root | `Environment=MALLOC_MMAP_THRESHOLD_=32768` in the unit (⭐ from the environment it **switches off the dynamic adaptation**: every frame above 32 KiB becomes `mmap`/`munmap`, and the defect stops being silent **forever**), then a large frame and `kill -STOP` to the browser for ~1 s ⇒ no ack ⇒ PTO ⇒ retransmission | `SEGV`, `error 4`, `ip` in libc, always in `__memmove_avx_unaligned_erms`. ⛔ **If it does not die, this diagnosis is wrong** |
| **B** — real loss | as A at point 1, then `netem loss 5%` and the film playing | it dies within a few seconds |
| ⭐ **C** — the proof that names the line | rebuild with `-fsanitize=address -g -fno-omit-frame-pointer` and redo A or B | `heap-use-after-free READ` with **two** stacks: the one that reads (`ngtcp2_pkt_encode_stream_frame`) and the one that freed (`coda_uccidi` ← `wt_scrivi`). ⭐ **It closes the case without margin** |

### 4.6 ⛔ The cure: why (a) and not (b)

- ⭐ **(a) the sober one — the one applied**: nothing is freed at serialization; it is marked
  `consegnato`, it is removed from the choice of `coda_scegli()`, and the `free` is done by the ack when the
  acknowledged offset covers `dati.n`, or by the closing/reset of the stream. ⚠ **Cost**: the memory of a
  frame stays committed for one more network round trip, and `WT_CODA_MAX` must be reread with that count
  in hand — 16 sessions × one more frame in flight;
- ⛔ **(b) the quick one — refused**: `ngtcp2_conn_shutdown_stream_write()` before the `free`, as
  `video_sgombra()` does. **It is not right here**: that one *resets* the stream, and §6.2 wants the frame
  **complete**. It would be **trading a rare crash for a frame broken always**.

### 4.7 ⏳ The trap to arm anyway — ⛔ not armed

Even with the cause in hand, **the machine was not equipped to have a death told to it**.

1. ⛔ **no core dump** ⇒ install `systemd-coredump`, **or**
   `core_pattern = /media/REMOTIX/tmp/09/core.%e.%p.%t` (**absolute**). `LimitCORE=infinity` is already there;
2. ⛔ **the log is shared and gets buried**: the tail of 08:28 sits in the middle of a 22 MB file
   and the following rounds write over it ⇒ an `ExecStopPost=` that, if the exit code is not 0,
   copies the last ~2 000 lines into `morte-%t.log` **together with `dmesg -T | tail -50`**;
3. ⭐ **`dmesg` must be collected ALWAYS at shutdown**, not only when someone remembers it: it is
   what saved the day;
4. ⭐⭐ **`MALLOC_MMAP_THRESHOLD_=32768` + `MALLOC_PERTURB_=165` on the bench.** The first turns
   every **large** use-after-free from silent to fatal; the second fills the freed memory with `0x92…`,
   so that even the small cases stop looking like good data. ⛔ **On the bench, not
   in the product**: they are slow.

### 4.8 ⛔ What of this diagnosis remains `[?]`

`[?]` **The retransmission was not seen with the eyes.** The log does not count lost packets
and the core is not there. The chain — violated contract → `frame_chain` that keeps the pointer
→ `rtb_on_pkt_lost` → `streamfrq_push` → `ngtcp2_pkt.c:1619 ngtcp2_cpymem()` — is read **line by
line in the ngtcp2 code present on the machine**, not observed in flight. ⇒ Until §4.5 runs,
it is a **probable cause with the line**, not a seen cause.

⭐ `[M]` **Everything else is measured**: the `dmesg` line, the instruction at `0x162B49`, the contract
in `ngtcp2.h:5246-5250`, the `cpymem` at `ngtcp2_pkt.c:1619`, and the count **1 out of 45 005**.

---

## §5 · ⭐⭐ THE FIVE CURES — the why, the price, and what each one does NOT do

> ⛔ **The diff is not here.** It is in `src/`, and the comments in the code are the seat of the reasoning: where
> this document would repeat a comment, it cites `file:line` and stops. What remains here is **the
> why of the choice**, **the price** and **what was discarded**.

### 5.1 ⛔⭐ Cure 1 — the crash · `webtransport.c:745-870`, `:5929`

See §4 in full. ⛔ **No switch**: it does not change what is seen, it corrects a way of
dying. ⚠ **Not verified**: the recipe of §4.5 was not run.

### 5.2 Cure 2 — the queue threshold in `video_sgombra()` · `webtransport.c:2705-2800`

**The defect**: there was no condition between *«a more recent frame exists»* and
*«abandon»*. On a narrow line a delta does not get out in 33 ms ⇒ the condition is **always true** ⇒
the abandon is **always**, and every abandon rekindles the debt of §5.2.

⭐ **The new rule, and it lies entirely in one word of `RCP.md`**: `:1156` says that the server **MAY**
call `RESET_STREAM`, not that it **MUST**. ⇒ a delta is abandoned **only if the video queue does not
empty within the threshold**. Below the threshold it is **kept**: the streams are independent
(`RCP.md:1155`), so keeping it **does not block** the following ones.

⛔ **The threshold is 100 ms, and the four constraints that derive it** *(⚠ derived, not proven: the
bench sweeps it at 50 · 100 · 200 and whoever chooses is the user, because it is a price that is SEEN)*:

1. **more than one frame period**, or it is today's rule with a new name: `[M]` phase 8, the
   real content goes at **20.9 fps = 47.8 ms**;
2. **less than the bottom with which a keyframe is already requested** — `WT_CHIAVE_RICHIESTA_MS` = 150;
3. it must **let a KEYFRAME plus a few deltas through** where the defect bites: `[M]` a keyframe
   on the user's canvas measures **20 817 bytes**; at 3 Mbit/s it gets out in **56 ms**, and in the 44 that
   remain **three deltas** fit;
4. the price adds to the loop: `[M]` phase 8, the whole loop is **55.20 ms**, and 100 + 55 stays
   below a fifth of a second.

⚠ **The declared fallback**: as long as ngtcp2 has neither `smoothed_rtt` nor `cwnd` **the
floor** is assumed, 20 Mbit/s = 2 500 bytes/ms — and **the log line says which of the two cases it is**, instead
of passing an invented number off as measured.

⚠ **And what the cure does NOT change**: `RCP.md:1165-1203` gives the abandon **three forms** — **A**
(stream reset, if a byte had already left) · **B** (hole in the `numero`, if no byte had left)
· ⛔ **C** (the missed credit: **no stream, no hole, no signal**, defect B-18).
⛔ **Which of A and B the client sees is decided by neither side**: it depends on whether a
byte had left. ⇒ The cure **does not touch this**: it changes **how many times** it happens, and **form C
it does not touch at all**.

#### ⛔ The edge cases, named so they are not discovered later

| case | what happens |
|---|---|
| **a KEYFRAME in the queue** | it is **never** abandoned (`RCP.md:1256`). ⚠ But its bytes **count in the sum**: with a keyframe in the queue the threshold is exceeded earlier and the deltas **behind** it go first — **which is right**, they would arrive after it anyway |
| **no estimate** | fallback at 20 Mbit/s: if the real line is narrower the fallback **underestimates** the wait and one delta too many is kept, for one network round trip |
| **full list** (32 slots) | a frame outside the list is not abandonable **and its bytes do not enter the sum** ⇒ queue underestimated. ⚠ Today it cannot happen: §2.3 grants 16 uni streams, the credit runs out first |
| ⛔ **the moment of crossing** | a delta is abandoned **and** the one just arrived is in turn a delta ⇒ `rcp_video_apri()` refuses it and **two are lost**. ⏳ `[?]` The remedy — requesting the keyframe **first** and abandoning when it arrives — is not in this cure and must be measured before writing it |
| **the scene stops** | `video_sgombra()` runs only at the arrival of a frame ⇒ with a still desktop it does not run, ⭐ **and it is not needed**: without new frames there is nothing to abandon |

#### ⛔⛔ And the partial refusal, which is the most important part

**«Dropping frames while keeping the deltas» — `RCP.md:1284` and `SPECIFICHE.md` §8.3 — CANNOT be done in
`webtransport.c`, and this cure does not do it.** The encoder runs with an **infinite GOP**
(`chiavi_ogni = 0`, `figlio.c` — ⚠ `[R]` `rcp.c` still cites it as `figlio.c`, which
today is another function: **expired reference**): every delta predicts from the frame **encoded**
before, not from the one **sent**. ⇒ Any frame the transport skips — abandoning it (forms
A/B) or not accepting it (form C) — **breaks the chain and costs a keyframe all the same**.

⭐ **The only place where the rate is lowered without breaking the chain is the stage**: capturing and
encoding less often. ⚠ And the neighbouring route is already closed by a measurement: Intel does not produce
**temporal sub-layers** (`EncRateControlExt` absent on **7 profiles out of 7**,
`sps_max_sub_layers = 1` on **6 cells out of 6**).

⇒ ⭐ **This cure is a prerequisite, not the cure of the phase.** Without it the regulator of §6
would be born on top of a transport that abandons anyway at every frame, and it would be impossible to measure
what it did.

### 5.3 Cure 3 — the quality climb-back · `codificatore.c`, `:141-143`

**The defect** `[R]`: `qualita_corrente` was **monotonic in the worse direction**. Four writes in
all (`:1880` the seeding, and the three inside `abbassa_qualita()`), **all going down**. The climb-back was searched for
and not found in six places — `codificatore_ridimensiona()` reopens the context and **keeps**
the value; `chiudi_contesto()`/`apri_contesto()` **read** it; no `alza_qualita()` in the whole of
`src/`; the `struct` is private to the file. ⇒ **The degradation lasted as long as the session.**

⛔ **And for a DELTA it is not one rung: it is three in one go.** `abbassa_qualita()` is called
**before** the check of the attempts ⇒ the delta that is abandoned in the end has nevertheless already
taken the ladder down **26 → 35 → 44 → 51**. ⇒ A single grainy delta brought the encoder to
QP 51 **and left it there forever**, and the abandon of the delta was declared in the log while the
permanent degradation **was not**.

⭐ **Where it is reachable, measured** — and it is the reason why the cure is small and not urgent:

| | does the ratchet fire? |
|---|---|
| `[M]` user's canvas 2560×1080, QP 26, 404 real keyframes: max **21 433 bytes = 0.13 %** of the cap, margin **782×** | ⛔ **no** — not even uniform noise gets there (15.1 %) |
| `[M]` 7680×4320 in hardware, real desktop | ⛔ no (1.5 %) |
| `[M]` 7680×4320, grain `alls=60` in hardware | ⚠ **94.9 %** — **at the border** |
| `[M]` 7680×4320, uniform noise in hardware | ⛔ **yes**, 8 out of 8 |
| ⛔ **software fallback**, 7680×4320, grainy clip | ⛔ **yes** — ⚠ the measurement (`libx264`) no longer holds after phase 18 |

⇒ Reachable by **one single narrow way**: the large canvas **plus** the software fallback. And the two
hold hands: `[M]` `h264_vaapi` on this chip stops at **4096 px per side**, and the legal canvas
of `RCP.md` §4.5 goes up to 7680 ⇒ **beyond 4096 the software fallback is not an eventuality, it is
the rule**. ⚠ after phase 18: OpenH264 stops at 4096×2304; beyond that, H.264 needs the card
(`DECISIONI.md` §10.26).

⛔ **The real bite is not the lost frame: it is what remains after.** The grainy frame lasts
one second; from there on the desktop — text, windows, still scene — came out at **CRF 47** or **QP 51**
**for hours**, and no line said why. ⇒ It is the *«never blur»* of `DECISIONI.md` §3.3 lost
**by inertia** instead of by decision.

**The constraint that decides WHERE the code goes**: `chiudi_contesto()` does `av_packet_free()` ⇒ the climb-back
**cannot** sit after `break`, where `fuori->dati` points inside the packet: it would be the same
defect as §4. ⇒ **counting at delivery, climbing back at the entry of the next frame**, and as a
side effect the cost of the reopening (`[M]` **91-108 ms** in hardware; the software one, measured with `libx264`, no longer holds after
phase 18) falls **between** two frames.

⛔ **And it is not symmetric to the descent, on purpose**: one goes down three rungs in one frame, one
climbs back **ONE** every `RISALITA_ATTESA`, with the wait that **doubles** at every relapse
(`RISALITA_ATTESA_MAX` ≈ 64 s). ⚠ The three numbers are `[?]` **sufficient, not right**, like
`CRF_PASSO` = 9.

⭐ **Why it does not violate I1**: I1 speaks of the **rate**, this cure of **quality** — and the two levers
were already separated by the user (§3.3: *«si calano i fotogrammi. Mai sgranare»*). ⇒ The cure does not touch the
lever of I1: it **gives back** the one of §3.3. ⛔ The only point where it could touch the rate is the
**reopening**, and that is why the wait doubles — without it, a scene at the border would do one
reopening every 2 seconds, **and that would indeed be I1**.

⛔ **The fault that would kill this cure is called THRASHING, and it is not hypothetical**: the grain
`alls=60` at 7680×4320 sits at **94.9 %** of the cap, that is it is a scene that lives **exactly on the
border**. In software a few rounds would be enough (the reopening costs much more than in hardware) for **the cure to cost more than the
defect**, and the one paying would be the **rate**. ⇒ The bench that decides is in §7.3.

### 5.4 Cure 4 — the audio reorder · `pagina.html` · `avvia_audio()`, `:5992`, `:6507`

**The defect**: `pagina.html` discarded by comparing with the **last datagram ARRIVED**, while
`RCP.md` §6.3 says *«already **consumed**»*. ⇒ **material was thrown away that would fit fifty times
inside the cushion already paid for**: a datagram overtaken by **1 ms** destroyed while **250 ms** of
buffer sit still doing nothing. The imbalance between the damage and the reserve is **1 to 250**.
⚠ The discard costs a hole of **5 ms** (PCM) or **20 ms** (Opus), **audible**.

`[M]` **The measurement that proves it**, with `netem`: a **fixed 30 ms** delay (which does not reorder) ⇒
purity **1.000**; **jitter ±2 ms** ⇒ purity **0.175**, with **1 004 datagrams discarded out of 4 989**
(20 %). ⇒ ⭐ **It was not the delay: it was the reordering**, and the cure is **free**.

⭐ **The frontier already existed and did not need adding: it needed CALCULATING.** `a.base` carries a server
`istante` into the clock of the `AudioContext`, `ctx.currentTime` is the playhead ⇒
`frontiera_us = (ctx.currentTime − a.base) × 1e6`, and a block is *already consumed* **if and only if**
`istante < frontiera_us`. ⛔ **It costs zero memory and zero delay**: it is a subtraction on numbers that
existed before.

⚠ **And `a.ult_ist_us` could not act as the border** even though it was the natural candidate: it is written in
`onended`, on the main thread — the one that stops to decode frames — it is not monotonic
as soon as out-of-order ones are accepted, and `ult_quando_perf`/`aoff` hang on it, that is **the yardstick
of the audio-video distance**. ⇒ Making it the border would mean making the yardstick depend on the reordering.

⛔ **The second piece is necessary, and without it the cure would be worse than the defect**: the page
treated *«the place of this block has passed»* as **one single case** and re-armed the anchor, that is it
moved the whole playback forward by **250 ms**. Right when **the playback** is
late, very wrong when **a single block** arrives behind a newer one: one would
pay **250 ms for a 5 ms block**, at every overtaking. ⇒ `a.ist_max_us` separates the two cases.

⭐⭐ **And along the way a defect was found that was not in the mandate**: the sentinel
of the *«fake anchor»* compared with `a.ult_ist_us` — the last **FINISHED** block, old by a whole
cushion. At regime `salto ≈ 250 000 µs` and `passo_us = 5 000` ⇒ `salti_suono` gained **~49
points at every healthy block** ⇒ the condition `salti_suono === 0` **could never be true**, and the
line that watches the hypothesis on which the whole anchor cure rests **was dead**. Repaired with the
same variable the cure introduces.

⛔ **And the price is ZERO, with the sign opposite to what `SPECIFICHE.md:128` fears**: no
intermediate buffer, no reorder queue, `AUDIO_CUSCINO_MS` **is not touched**, 4 integers per
session. ⭐ Every cured overtaking is a re-arm **saved**, and a re-arm costs `+250 ms` ⇒ under
reordering the cure **lowers** the average delay.

⭐ **And the comfortable cure that this constraint kills, written so that nobody fishes it out again**: *«we keep the
datagrams in a queue ordered by `istante` and deliver them with a fixed delay»*. It is the classic jitter
buffer, it is what everybody writes, and **it would sell X ms of response to buy the
smoothness the anchor already gives for free** — the anchor *already is* the de-jittering. ⇒ It would be **250 ms
paid twice**.

#### ⚠ The honest question: does it really bite, or only under `netem`?

⭐ `[M]` **On real WiFi the «vecchi» are zero.** ⇒ **On the user's path of today this defect
does NOT bite, and whoever presented this cure as an improvement of what he hears now
would be lying.** And the reason is mechanical, not luck: **802.11 already reorders by itself** (a QUIC flow sits
in a single TID, the receiver keeps a block-ack window with reordering) ⇒ WiFi **loses** and
**delays**, but **does not overtake**. The same for a cable and for loopback.

⚠ And `netem` overtakes so much for a reason that must be written or the bench looks harsher than reality:
`delay X Y` gives **every packet** an independent delivery time, and the child sends the datagrams
**in bursts**, microseconds apart ⇒ **inside a burst, any jitter reorders.**

**So why cure it anyway**, in three arguments and not an opinion:

1. ⛔ **the project's declared path is not WiFi**: **QUIC migration** is, by
   construction, packets in flight on **two paths at the same time** that arrive interleaved —
   it is `netem` done by the protocol itself. And the audio datagram on a non-local network has never been
   measured;
2. ⛔ **the failure mode is disproportionate**: 20 % discard ⇒ purity **0.175**, that is audio
   destroyed. A defect that stays at zero as long as the path is clean and then **takes the sound away
   suddenly** at the first network that overtakes arrives without warning, and it arrives on the user's phone,
   **that is where the bench is not**;
3. ⭐ **the price is zero**. Free insurance against a **total** failure mode is bought.

⇒ ⛔ **It is declared for what it is: a conformance to §6.3 and an insurance on the paths not yet
measured, NOT an improvement of what the user hears today.** The control measurement on real
WiFi must give **identical to before**, and if it gave something different it would be the cure that has a defect.

⚠ **And the warning already paid for remains**: the measurement is in **5 ms PCM**. With Opus (20 ms) the
overtaking threshold is **four times higher** and the defect bites four times less ⇒ the real path is
Opus, and on Opus the `[M]` number **is not there**.

⛔ **What IS verified of this cure, and what is not**: §3.16.

#### ⛔ The four audio cures **discarded**, and why — *written so that nobody fishes them out again*

| discarded cure | why |
|---|---|
| **lowering `AUDIO_CUSCINO_MS`** | the code expressly forbids it **here and now**: first one measures **the arrival jitter**, which nobody has measured. ⭐ And this cure **produces that measurement** (`fuori_ordine` + the discards) ⇒ it is the step that goes **first**, not instead |
| **a reorder queue with fixed delay** | 250 ms paid twice, and it sells response |
| **removing the discard altogether** | §6.3 imposes it, and without a border a really old block **would overlap what is playing** — finding 3 of 17 Aug all over again |
| **the `AudioWorklet`** | it is another thing, and it is already declared: the numbers of 21 Aug say that **this** is not the problem |

⚠ **And a falsification that holds for the whole bench**: if after the cure purity rises but
`usciti` does **not** rise with it, ⛔ **the sound is not there** — and it has already happened in this file: a
session **mute with all counters green**.

### 5.5 Cure 5 — the bandwidth cap · `codificatore.c:200-340`, `:1786-1800`

**The measurement that makes it compulsory**: §3.8 — with **fixed QP 26 and no cap**, hard content at full
screen asks for **58.668 Mbit/s = 293 % of the floor**, and nobody tells it no.

⭐⭐ **And the mode was chosen with the bytes, not with a preference** — measured on the laptop on 23
Aug in the afternoon, the detail in `codificatore.c:200-260`:

| mode | outcome |
|---|---|
| ⛔ **VBR** | **out**, and the proof is not a reasoning: with and without `qp=26` **the very same bytes** come out (8 350 170 and 514 142, two times out of two) ⇒ **under VBR the `qp` is ignored**, and the whole degradation ladder **plus the climb-back written this morning** would become **silent no-ops** |
| ⛔ **CBR** | **unmasked on our own hardware**: with a still scene it spends **15.98 Mbit/s against 0.193** for CQP — **83 times** for nothing (R31 of v1 said 42× at 1440p: **here it is worse**) |
| ⛔ **ICQ / AVBR** | out: never measured, never seen in v1, and `AVBR` converges *«in N frames»* — a mode that settles over a window is wrong **precisely at the instant the scene changes** |
| ⭐ **QVBR** — **chosen** | the ladder **HOLDS**: `[M]` still scene QP 26 → **0.218** · QP 35 → **0.125** · QP 44 → **0.076** Mbit/s. ⚠ And with a **hard** scene the ladder no longer bites (11.14 · 11.31 · 11.19): **when the cap is engaged the quality is decided by the cap, not by the QP** — it must be said, or a bench looking there for the effect of the QP would not find it and would conclude wrongly |

⛔ **The three numbers are derived from the floor, none is written by hand**: `rc_max_rate` = **80 %** of the
floor (16 Mbit/s ⇒ 16 + the **2.426** `[M]` measured for audio/input/QUIC = **92 %** of the
floor: the margin has a number under it instead of being prudence) · `bit_rate` = **75 % of the wire**,
⛔ **never equal to the wire, it is R31 to the letter** · `rc_buffer_size` = wire × **40 ms**.

⛔⛔ **And that third line is the one v1 got wrong without anybody noticing**:
`fondamenta/remotix-c/src/codificatore.c:256` set `rc_buffer_size = bit_rate / 2`, which **is not «half»:
it is half a SECOND** — a VBV is measured in bits, and `bit_rate/2` bits at `bit_rate` bits/s make **500 ms**,
that is **ten times** the 50 ms cap that `CODER.md` §1-bis gives to **the whole** of our piece.
⭐ Here it is **40**, that is the *target* and not the *cap*: it errs in the uncomfortable direction. ⚠ And the
number is not deduced, it is **printed by ffmpeg**: `[M]` *«RC target: 75 % of 16000000 bps over 40 ms»*.

⭐ **And a red predicted by the study has already FALLEN**: declaring 16 Mbit/s ffmpeg prints
`Using level 5`, that is **5.0** ⇒ **bandwidth does not raise `level_idc`** and `avc1.640033` holds.

#### ⛔⛔ And the THREE witnesses, because one alone is not enough — *R31 does not say «write a log line»*

R31 says ***«it is asked for by name and one verifies that it obeyed»***, and verifying means **three
independent witnesses**:

| # | witness | what it proves | ⛔ what it does **NOT** prove |
|---|---|---|---|
| **1** | **the driver, before opening** — `VAConfigAttribRateControl` on the pair (profile, entrypoint) | that the mode **exists** on that pair | not that it will be used |
| **2** | **the context, after `avcodec_open2`** — `rc_mode`, `bit_rate`, `rc_max_rate`, `rc_buffer_size` **reread** | that **libavcodec** kept what it was asked | ⛔ **not that the driver applied it** |
| **3** ⭐⭐ | **THE BYTES** — bytes/s with a still scene against bytes/s with a moving scene | **which mode is really in force** | — |

⛔⛔ **The third is the only one that would have caught R31.** In v1 witnesses 1 and 2 would have been **all
green**: `bit_rate` and `rc_max_rate` were exactly the numbers requested, and **nobody had asked for
CBR** — CBR was **the name the driver gave to that pair of numbers**. ⇒ **Only the bill
said so.**

⛔ **And the question to the driver has THREE outcomes, not two**: *«I could not look»* ≠ *«the driver does not
declare it»* ≠ *«here is the mask»* — ⛔⛔ and the second **does not mean «there is only CQP»**. `[M]` The
trap is **already armed inside ffmpeg**, and it is a string in the binary: *«Driver does not report any
supported rate control modes: **assuming CQP only**»*. ⇒ If the driver is silent, **libavcodec decides by
itself** and goes on: it is R31 in a new form — not *«the driver deduces»*, but *«ffmpeg deduces on behalf
of the driver»*, **with the same silence**.

⭐ **And asking by name is not prudence: it is the only way to get a red instead of a
bill.** With `rc_mode = auto` something else is chosen **in silence**; with the name `avcodec_open2`
**fails**, and the parenthesis of the error *«(supported modes: …)»* **lists what there is**.

⚠ **And the bench rule that comes out of it, in one line**: ⛔ **the mode check is done with a
STILL screen** — `[M]` with a still scene the modes differ by **83×** (CQP 0.193 against CBR 15.98 Mbit/s), with a
hard scene they all lie within 1 % of each other ⇒ **a bench that measured only the hard scene
would measure nothing**. ⛔ **But on the product «still» means ZERO frames** (§3.8: 0.00
fps), so the scene that acts as control is **the second one: the real desktop**, which moves and costs
1 %.

⚠ **What is NOT touched, and it must be said**: `max_frame_size`. `[M]` ffmpeg refuses it under CQP and
accepts it under QVBR — it would give **in one pass** what today costs up to 3 reopenings of
91-108 ms. ⛔ It is not switched on today: it is a **second lever on the same quantity**, and two levers switched on
together at the first round would give **two measurements under the same label**.

#### ⛔ And the defect found along the way, which was not the target of the study

`[R]` **The server never reads `video.livello`.** `rcp.c` · `livello_legge()` lists it among the known names, and the loop
captures `c_codec`, `c_prof`, `c_audio`, `c_misura` — **not the level**. `RCP.md:701` says that the
server **MUST** emit a stream of a level not higher: **that MUST was not implemented**. The
rest of the chain was already there (the **real** level read from the bytes at `codificatore.c` · `tetto_serbatoio_bit()`, printed at the
first frame) ⇒ ⭐ **ONE comparison was missing between two numbers the product already has in hand.**
Since 23 Aug **the two lines are written** (§3.12) — ⛔ but **the comparison is still made by whoever reads, not
by the program**.

⚠ **And the symptom, if it bit, is the one `RCP.md` writes**: a level declared too low
**does not give a network error, it makes the decoder refuse the configuration** — that is **a screen that
does not start, without a red anywhere**. Same family as R31.

#### ⭐ And the level really bites, but **on pixels and frames**, not on bandwidth

`[R]` Two corrections that hold beyond the phase:

- ⛔ **`SPECIFICHE.md:1087` speaks of another codec**: *«tier High»* and *«40 Mbit/s»* are **HEVC**
  (Table A.9, level 5.1 Main tier = 40 000 kbit/s). **H.264 has no tier at all.** The line was
  correct **for the codec the product had when it was written**, and did not follow the change of
  17 Aug (*«AV1 esce, entra H.264»*);
- ⛔ **on bitrate the line does not bite at any value this product can produce**: for
  `avc1.6400xx` (High) the cap is **168.75 Mbit/s at 5.0** and **300 at 5.1** — 8.4 times the floor;
- ⭐⭐ **but `MaxFS` and `MaxMBPS` bite**: 2560×1080 (the user's canvas) requires **5.0** as a
  minimum — it is the reason, never written, why bench `07-b48` verified precisely `avc1.640032`.
  ⛔ And **at 3840×2160 5.0 does not fit at all**: 5.1 is needed, which grants `[?]` **30.3 fps**
  ⇒ **the «60 fps» of the wish list is not reachable at 4K even with infinite bandwidth**;
- ⚠ `[R]` **the product declares 5.1, not 5.0** (`pagina.html` · `LIVELLO_DICHIARATO()`) ⇒ `avc1.640033`. 5.0 lives in
  **two comments**, and one of the two (`codificatore.c:1559-1560`) is **stale**.

---

## §6 · ⏳ THE RATE REGULATOR — **designed, NOT written**

> ⛔ **It is the work that remains**, and it is the piece the phase exists for. No line has been applied.

### 6.1 The design on one page

| | |
|---|---|
| **the quantity** | ⭐ **`arretrato`** — how many **delta** frames in flight still have bytes **in our output queue**, read at the arrival of a new frame, **before** `video_sgombra()` |
| **the rule** | `arretrato == 0` ⇒ send · `arretrato >= POSTI` ⇒ **this frame does not leave**. No other lever |
| **the descent** | it is not a number being lowered: it is **a frame that does not leave**. The rate drops by itself, as much as the queue does not empty |
| ⭐ **the climb-back** | **does not exist, and this is the merit**: `arretrato` is reread at every frame, it is not remembered. ⛔ No ratchet — that is no `qualita_corrente`, which is the measured defect of §5.3 |
| **the bottom** | 480p·25 **is not a brake, it is a verdict**: if the delivered rate goes below 25/s on 20 Mbit/s, the log declares it a **defect**. Forcing a frame into a queue that does not empty makes the queue worse |
| **the log** | one line at the **start** and one at the **end** of every episode, never one per frame; plus a counter of its own, `video_ritmo_scesi` |
| **the switch** | `--ritmo-adattivo`, **off by default** (I6), and the value in force **written at startup in both cases** |
| **where** | `webtransport.c`, inside `video_a_una()`, three lines above `video_sgombra()` |
| ⛔ **the mandatory order** | **first the cure of `video_sgombra()`, then the regulator** — §6.5 |

`POSTI = 2`, and ⛔ **it is not a disguised clock**: it is the depth of the pipe. With `POSTI = 1` one would
skip every time the previous frame has not left **entirely** by the arrival of the
next — at 60/s that is 16 ms, and a 10 KB delta on a healthy line takes longer: it would be a
**prudent heuristic**, that is **I1 broken**. ⚠ `[?]` The value is tuned on the bench.

### 6.2 ⛔ Why `arretrato` does not fall back into P13 and P20

- **P13**: the tolerance said *«for one second»*, and it was corrected two hours later — *«the second was the
  wrong quantity: what must empty is a **queue**, and how long a frame already
  in flight takes depends on the **bandwidth**, not on the clock»*. ⇒ `arretrato` **is the queue**, counted in
  frames: one does not ask *«has too much time passed?»*, one asks *«are the earlier bytes still
  here?»*;
- **P20**: the cure was **what the client itself sent — local, monotonic, independent of
  delivery**. ⇒ `arretrato` has exactly that shape on **our** side: bytes produced by us and
  still in our house. **No lost packet, no reordering and no silence of the client can
  falsify it**, because nothing that comes from outside is looked at.

⭐ And the sentence is **already in the code**, written for the same reason: *«an estimate can be wrong, a byte
in the queue cannot»*.

⚠ **And the three things `arretrato` is NOT**: it is not a **target rate** (if it existed it would have to
climb back, and someone one day would forget to make it climb back — **it has already happened**, §5.3); it is not
the **bandwidth** (`cwnd/rtt` is an estimate, and as the input of a loop that decides whether a frame leaves
it would be a calculated number in place of a fact); ⛔ **it is not a client ack** — §6.6.

### 6.3 ⭐ What ngtcp2 already gives us measured and today we do not look at

`ngtcp2_conn_get_conn_info()` fills **seven** fields. Today it is called in **one single place** and
**two** of them are read.

| field | today | what it would say |
|---|---|---|
| `smoothed_rtt` · `cwnd` | ✅ | the network round trip and the granted window |
| `bytes_in_flight` | ⛔ **never read** | ⭐ it is **the piece of backlog our queue no longer sees** — the code already declares it as a hole |
| `min_rtt` | ⛔ never read | ⭐ `smoothed_rtt − min_rtt` **is the queue inside the network, in milliseconds**: it is the number with which one **honours** `SPECIFICHE.md:128` instead of citing it |
| `ssthresh` | ⛔ never read | distinguishes *«the line is rising»* from *«the line has given way»* |
| `latest_rtt` · `rttvar` | ⛔ never read | the jitter, for audio |

⛔ **And the congestion algorithm was never chosen**: ngtcp2's default is taken
(CUBIC). ⚠ **It is not changed inside this design** — it would be a second variable in the same
bench — **but the item must be opened**: on WiFi, CUBIC reads **a radio loss** as congestion
and halves the window; BBR, which ngtcp2 offers, works on bottleneck bandwidth and `min_rtt`, that is
on two numbers this design wants to read anyway. `[?]` **to be measured as a separate
experiment, behind its own switch.**

⚠ And a limit that is not ours: how much we can send on a stream is decided by the **client** with
`initial_max_stream_data_uni` / `initial_max_data`. ⇒ **A queue that grows with a HIGH `cwnd_left` is not
the line: it is the browser's window**, and the cure is another one.

### 6.4 ⚠ The declared price: cutting happens **downstream** of the encoder

The skipped frame **has already cost the child's GPU**. The real lever — not capturing it at all —
lies in the child, and the pipe to get there **already exists** (`figli_video()` already carries codec, depth and
keyframe across the process boundary).

⛔ **But it is not done in phase 9, and the reason is architectural**: the stage is **one per user**, the
sessions are **N**. A rate imposed on the stage would impose it on all of them, **and the session on the good
line would pay for the one on the bad line.** ⇒ `[?]` open, and it is worth reopening only with
the measurement of how much a wasted frame really costs — which with zero copy could be
little. ⚠ And a difference to our disadvantage, declared: **GNOME regulates before encoding, we
after.** On GPU consumption theirs is better.

### 6.5 ⛔⛔ THE CHECK THAT INVALIDATES THE WHOLE BENCH, and it comes before the others

**`video_sgombra()` empties the delta queue at EVERY frame.** As long as this is so, `arretrato` **is zero
by construction**: when frame N+1 arrives, the bytes of N have already been thrown away by the
previous round.

⇒ ⛔ **A regulator installed today would never fire, and the bench would read it as «the line
carries it».** They are two facts with the same face.

⭐ And the two changes are **one single change looked at from two sides**: `video_sgombra()` stops
throwing away the previous delta just because a more recent one has arrived (cure 2, §5.2), and the regulator
stops producing new ones at the same instant. ⛔ **Mandatory order: first the cure, then the
regulator.**

### 6.6 ⛔ What of GNOME's regulator is refused — and what is copied

⭐ **The shape is copied**: frame slots, no bitrate control, no adaptive
resolution, the loop that paces itself instead of chasing a target. ⛔ **The quantity is not**, for three
independent reasons:

1. **`ack_rate` does not exist for us.** The message table of `RCP.md` contains no
   frame acknowledgement. Copying it would mean a new type, a new obligation for the client, and
   **a network round trip inside the control loop** — that is buying the reaction with delay.
   `arretrato` costs **zero ms**: it is already in our memory;
2. ⛔ **`ack_rate` depends on delivery and on the peer's cooperation**, that is it is *precisely* the
   P8→P20 family. The client can suspend acknowledgements with `queueDepth == 0xFFFFFFFF` and **a
   regulator that does not handle it stops forever**. ⚠ And the trap **is not defused with an
   `if`**: a loop that the peer **can** freeze does not become safe because a special case is
   added. By asking nothing of the peer, the trap **does not exist**.
   ⇒ ⭐ Consequence to be written so that nobody looks for it: check **M1** of `STUDI.md:1173`
   (*«our regulator holds `queueDepth == 0xFFFFFFFF`»*) becomes **vacuous** — it must be marked **not
   applicable**, not left open;
3. ⛔ **GNOME's threshold is a disguised clock**: `delayed_frames = rtt_us × refresh_rate / 1e6`
   converts an RTT into a number of frames. It is **P13 in another dress**, and it breaks at the same
   point: a 60 KB keyframe does not take one RTT, it takes `byte × rtt / cwnd`.

### 6.7 ⚠ The honest question: at 20 Mbit/s is it really needed?

**At regime, no**, and it is the prediction of §7.4. ⇒ ⭐ **It must be judged for what it is: a parapet.** Its
correct behaviour is **doing nothing**, and a bench that proved only that it does not fire
would have proved **half** of the work.

**Where it really bites**, in order of probability:

| | why |
|---|---|
| ⭐⭐ **WiFi → mobile network migration** | the path changes, ngtcp2 **resets the congestion control**: `cwnd` goes back to the initial window, ~10 packets ≈ 14 KB. ⛔ **A 60 KB keyframe does not fit**, and the queue forms with certainty. It is *«the best reason why QUIC was chosen»*, and today there is nothing governing it |
| ⭐ **the temporary WiFi drop** | a modulation fallback brings 200 Mbit/s to 15 for one or two seconds — ⭐ **and it is exactly the step measured in §3.10** |
| **other people's traffic on the same line** | the window narrows without the line changing |
| ⚠ **several sessions of the same user** | the stage is one, the sessions N; and downstream there is the network budget (ten × 20 = **200 Mbit/s**) |
| ⛔ **NOT at regime on a healthy 20 Mbit/s line** | and it is the prediction this phase must confirm first |

⇒ ⭐ **Consequence on the bench, and it is not a detail**: **throttling at a constant 20 Mbit/s does not prove
this design.** A **step** is needed — and it is the reason why §3.10 was measured that way. ⭐ And the
control of §3.10 (`pieno`, which asks for less than the hole: **nothing moves**) proves that the bench does not
fire blanks.

### 6.8 What the design does **not** touch, declared

the **QP** (stays fixed at 26: doing it here would mean two variables in the same bench) · the **congestion
algorithm** (§6.3 opens the item and does not close it) · the **resolution** (out by decision) · the
**audio cushion** (it has nothing to do with bandwidth) · ⚠ and **no new intermediate buffer**: it is the only
way in which `SPECIFICHE.md:128-131` is honoured without having to justify it in milliseconds.

---

## §7 · ⛔ THE DESCENT LOG — and the predictions awaiting measurement

> ⛔ **Why the log belongs to this phase and is not an accessory.** I1 does not only say *when* one may
> drop: it says that **«every descent is declared in the log»**. ⇒ ⭐ **A regulator that goes down
> without saying so is indistinguishable from a defect.**

### 7.1 ⏳ The shape of the line — ⛔ designed, **not applied**

`[R]` No rate regulator exists, so the line must be **designed first**, or it will be born as
prose. ⛔ **Not prose**: one single line, fields in fixed order, `chiave=valore`, so that a bench
reads it with `split()` and not with a regex on Italian prose.

```
🔻 RITMO  chi=nic/198.51.100.7  da=60  a=40  unita=fps
          causa=coda_video  misura=1843210  soglia=1500000  unita_misura=byte
          per=I1/§8.2  attivo_da_ms=0
```

| field | why it cannot be removed |
|---|---|
| `🔻`/`🔺` | ⭐ the **climb-back** is half of the invariant: a regulator that goes down and does not climb back **has dropped out of prudence with an hour's delay**. The ratchet of §5.3 was already this defect, measured |
| `da=` / `a=` | without the **before**, «40 fps» is not a descent: it is a number |
| ⛔ `misura=` **and** `soglia=` | **it is the field that makes I1 verifiable without trusting the code**: if `misura < soglia`, that descent is **out of prudence**, and the line itself proves it |
| `causa=` **closed label**, not a sentence | a bench counts the descents by cause; an Italian sentence cannot be counted |
| `unita_misura=` | *«the right number and the wrong word beside it»*: bytes and kbit/s already live together in this file |
| `attivo_da_ms=` | ⭐ without it, a descent and climb-back alternating 20 times a second (**oscillation**) have the same log as a stable descent |
| `chi=` | four sessions on the same log file |

⭐ **The same shape holds for quality** — `🔻 QUALITA modo=QP da=26 a=35 causa=tetto_16MiB …` — and
it is the line that `abbassa_qualita()` **does not write**: it writes only the two *failures*. ⇒ For a **delta**
the ladder goes down **26 → 35 → 44 in silence**.

⛔ **And the line is written only when the value CHANGES**, not at every frame: so the log *is*
the rate curve, and the cost is the number of descents, not the number of frames. ⚠ With an **oscillation
bottom**: if it changes more than *N* times a second, the line becomes *«🔻🔺 RITMO PENDOLA»*, which
is **a defect of the regulator** and must be stated as such.

### 7.2 ⛔ The holes the inventory found — and one was already closed

`[M]` **How much a line costs**, measured on 23 Aug on Intel N100 (the **slower** hardware of the two,
so it is a cap): **0.63 µs** and **98 bytes**.

| | |
|---|---|
| ⭐⭐ **one part of the mandate is REFUSED**: the **third form** of the abandon (the missed credit, defect B-18) **is written in the log**, always on, with the debt cure beside it | ⇒ The hole is not there. **Two reservations of form** remain: the line **has no bottom** (under famine it writes 60 lines/s per session, ⚠ and it is the shape of the **30.8 GB**), and the count comes out **only at the end of the session** |
| ⛔ **the keyframe debt: seven reasons in nine points, not five.** The comment declares *«FIVE points»* and already bears the scar of the previous time (*«it said three and the points were four»*) | ⭐ The notable thing is not the number: it is that `serve_chiave_perche` **exists and carries the reason up to the line** ⇒ **the quantity the bench needs is already there, and already has the right shape** |
| ⛔ **four descents ALREADY exist in the product, and three are silent** | `abbassa_qualita()` on a delta (26→35→44, **without the number**) · the **ratchet** (no accessor to read it from outside) · the oldest audio block thrown away because the queue is full (⚠ **the twin three lines above has the line**, and the comment says why) · ⭐ the **rate at zero** when the encoder does not open, which **is** declared with the number |
| ⛔ **`*come` of `chiave_intervallo_ms()` ends up in verbose mode** | The comment above the function declares that *«it is the only thing that distinguishes "the cure is working" from "the cure is not switched on yet"»* — **and then writes it in verbose mode** ⇒ in every normal installation the two have exactly the same face. **It is principle 2 violated inside the function that cites it** |
| ✅ **the values in force at startup** | ⭐ **applied on 23 Aug**: §3.12. ⛔ But the **floor** (480p·25 and 20 Mbit/s) **does not exist in the code yet**, and it must be written **even if the regulator is not there**: it is the number below which the phase has no permission to go |

### 7.2-bis ⚠ THE PRICE — and ⛔ **an intermediate level is not needed: a BOTTOM is needed**

`[M]` 0.63 µs and 98 bytes per line. `[R]` At regime, **one** session at 60 fps, the lines **per
frame** are two (`stream uni aperto` and `codec N: … byte`):

| | lines/s | bytes/s | in an hour | CPU |
|---|---|---|---|---|
| **one session, with `--parlantina`** | **120** | **11.8 kB/s** | **42 MB** | **0.0076 % of a core** |
| four sessions | 480 | 47 kB/s | 170 MB | 0.03 % |

⇒ ⭐ **CPU is not the price: it is three hundredths of a thousandth of a core.** The price is the **disk** and
**readability** — a log in which the two lines per frame bury everything else in a
ratio of **120 : 1**.

⛔⛔ **And under congestion the price is paid even by the log when it is OFF.** `[M]` 21 Aug: at 3 Mbit/s
the line *«FOTOGRAMMA NON SPEDITO»* comes out **28 times a second**, and every abandon generates another one
⇒ ~**60 lines/s = 21 MB/hour without `--parlantina`**, and **neither of the two has a bottom**.
⇒ ⛔ **The log is noisier when the line is worse, that is when it needs reading.**

⛔ **A third level (`--parlantina-ritmo`) is the wrong road**: it would put the I1 lines
behind a switch off by default, and ⛔ **a descent declared only when someone has switched on
a switch is NOT declared**. ⇒ Principle 2 and I1 impose `registro_dice()` for every
`🔻`/`🔺` line. ⭐ **What is needed is the bottom**, and the product already has **four working forms** of it,
all with the motivation written beside them: *only once* (`bool detto`) · *every N*
(`== 1 || % 100 == 0`) · ⭐ *when it changes by ≥ threshold* (**the shape of the `🔻`/`🔺` lines**) ·
⭐ *once a second, with the ZEROS inside* (**the shape of the periodic rate line**).

⇒ **The proposal, in four points and without a new level:**

1. the `🔻`/`🔺` lines at `registro_dice()`, **only when the value changes** ⇒ on a healthy session:
   **zero lines**;
2. a `ritmo:` line **once a second, always, with the zeros inside** — frames delivered ·
   skipped for credit · abandoned · bytes in the queue · value in force. **98 bytes/s per session =
   0.35 MB/hour**: **120 times less** than verbose mode;
3. ⛔ **a bottom on the three lines that under congestion come out at 28-60/s.** ⚠ And it cannot be put
   **before** the periodic line of point 2, because today the count comes out only at the end of the session: they are
   **one single cure in two pieces**;
4. ⚠ and, **outside the mandate of this phase**, the **filter by area** (`--parlantina wt,rcp`): today
   verbose mode is a single switch over **eleven** areas, and whoever investigates the rate carries along
   the clipboard, the keyboard and the cursor.

### 7.3 ⛔ The checks that decide — *which fault brings down each thing*

⭐ *«A check must read something that can be **WRONG**, not something that can be averaged.»*

| the thing | the fault that brings it down |
|---|---|
| `🔻 RITMO` exists | ⛔ **the rate drops with a still scene**: **one single** `🔻` line in 60 s of still scene ⇒ red |
| `🔺 RITMO` exists | ⛔ **the ratchet**: throttle 10 s, remove the throttling, wait 10 s — no `🔺` ⇒ red. ⚠ **Today quality would fail this bench** *(as long as `--qualita-risale` is off)* |
| `misura=` / `soglia=` | ⛔ `misura < soglia` in any `🔻` line ⇒ **red, and nothing else is needed** |
| `attivo_da_ms=` | ⛔ **oscillation**: > 4 changes/s ⇒ red |
| startup line with the values | ⛔ **form E1**: start with `--qp 40`, read the line — if it says 26, the switch does not reach the encoder |
| **the climb-back** (cure 3) | ⛔⛔ **THRASHING**: grain `alls=60` at 7680×4320 for 60 s continuously — more than **3 reopenings per minute** after the first minute ⇒ red. ⭐ **It is the check that decides**: if the doubling wait does not switch it off, the three numbers are wrong. ⚠ And the case to believe in is **I1 paired**: frames/s **with** the cure lower than those **without** ⇒ red |
| the **floor** of the climb-back | ⛔ 10 000 empty frames: if quality goes **below** `richiesta.qualita` even by one rung ⇒ red |
| the **lossless** | ⛔ re-entering LOSSLESS ⇒ red: it would be the change of quantity mid-session |
| ⛔ the **memory** | 10 000 descents and climb-backs in a row: `valgrind` finds a GPU surface not returned ⇒ it is the defect *«that only shows after half an hour»* |

### ⛔ And a line that is REFUSED, by the same rule

*«estimated bandwidth = N kbit/s»*, written once a second. **There is no fault that brings it
down**: `cwnd/rtt` is an **averaged** quantity, plausible in every condition, and a bench that
reads it cannot tell whether it is right. ⇒ ⭐ **It must not be written.** What must be written is the **byte in the queue**
— which can be wrong — and the bandwidth only **inside** a `🔻` line, as *proof of the threshold*.

### 7.4 ⛔⛔ THE FALSIFIABLE PREDICTIONS AWAITING — **the pact of the phase**

> ⚠ **They are all kept.** They say what we expect and what would refute us, and they serve the
> day of measuring. ⭐ Where the prediction is also in the code, the code is the seat: here there is
> only the line, with the `file:line` beside it.

| # | the prediction | ⛔ what would refute it | where in full |
|---|---|---|---|
| **P1** | ⛔ **the crash reproduces** with `MALLOC_MMAP_THRESHOLD_=32768` + frozen client: `SEGV`, `error 4`, always in `__memmove_avx_unaligned_erms` | **if it does not die, the diagnosis of §4 is wrong** | §4.5 |
| **P2** | **the queue threshold is INERT at 20 Mbit/s**: `abbandonati per soglia` = 0, loop delay = 55.20 ms | ⛔ **many abandons per second with the switch off at 20 Mbit/s** ⇒ the defect bites **above** the floor, the cure is not a robustness measure, and **it changes the priority of the phase** — §10.2 | `webtransport.c:2738-2790` |
| **P3** | **on the step** (3 s at 10 Mbit/s, `barra`): fps in seconds 8-10 from 13-14 to **≥ 25**, keyframes/s from 6-7 to **≤ 2**, abandons/s **≤ 2**, seconds 7 and 12 **identical** | ⛔ **4 reds**: (1) keyframes stuck while the abandons go down ⇒ the debt is kindled by **another** of the seven causes, almost certainly the **missed credit** (form C, invisible to the receiver); (2) fps do not rise ⇒ threshold too high, go down to 50; (3) ⭐ **the loop exceeds 55 + threshold** ⇒ the estimate **underestimates**, and it is the most important red because it would be **a number that looks measured**; (4) the return stops being under a second ⇒ the cure pays for the transient with the return, and must be **switched off** instead of tuned | `webtransport.c:2738-2790` |
| **P4** | **the bandwidth cap**: `ferma` 0 · **real desktop 0.20-0.45** · flat colour 1.1-1.6 · halftone **11-16** · grain **11-16**, and **NEVER above 16** | ⛔ **2 change the conclusion**: (1) ⭐⭐ **the real desktop costs LESS than 0.204** ⇒ the cap **saves where it must not**, it is v1 repeating itself, **and this cure is thrown away** (the prediction is *«it does not go down»*, and it is flat: `[M]` on the laptop QVBR spends **13 % more** than CQP with a still scene); (2) ⭐⭐ **the halftone stays above 20** ⇒ the driver **did not obey**, R31 holds **even against the explicit request**, and **only the third witness, the bytes,** catches it | `codificatore.c:252-300` |
| **P5** | **the quality climb-back**: after a grainy burst and 600 still frames, the confession goes back **exactly** to 26 (or 20) and there is the `RISALITA` line | ⛔ **thrashing**: > 3 reopenings/minute on the scene at **94.9 %** of the cap ⇒ the three numbers are wrong; and ⛔ **fps with the cure lower than those without** (paired, same scene) ⇒ the price is paid by I1 | §7.3 · `codificatore.c:100-145` |
| **P6** | **the audio reorder**, on the `netem` profiles: ±2 ms **0.175 → ≥ 0.95** · ±5 ms ≥ 0.95 · ±10 ms ≥ 0.90; `vecchi` from **1 004 to ~0**, and `fuori` must **take that number** ⭐ *(the strongest prediction: if the sum is not conserved, it is wrong)* | ⛔ **overlapping blocks** ⇒ purity **gets worse** and the judge hears **distortion, not holes** (⚠ it is the worst way of failing, and **it has already happened** in this file: finding 3 of 17 Aug) · **border too permissive** ⇒ `tardivi ≈ vecchi di prima`, the cure cured nothing · **border too strict** ⇒ high `vecchi` **with `fuori` at zero**, the anchor is drifting (distinctive symptom: `pieni` rises together) · `[?]` **Opus does not tolerate non-monotonic timestamps** ⇒ `errori` rises on the Opus path and stays **zero on PCM**: **not verified**, and the bench must be done on both codecs | §5.4 |
| **P7** | **the regulator, MOVING scene at 20 Mbit/s**: 20-37 fps (those the scene produces), `arretrato` **0, now and then 1, never 2**, `video_ritmo_scesi` ⭐ **0** | ⛔ **descents with a normal desktop** ⇒ `POSTI = 2` is too narrow or a frame costs more than measured (**the log line says by itself which of the two**) · **descents with a HIGH `cwnd_left`** ⇒ it is not the line, it is **the browser's window** · `video_saltati` growing with `arretrato` at 0 ⇒ the bottleneck is **the stream credit** · ⛔ **zero descents AND zero reads of `arretrato`** ⇒ it is not a confirmed prediction, **it is a loop never travelled** — §6.5 | §6 |
| **P8** | **the regulator, STILL scene**: `video_ritmo_scesi` **unchanged**. ⭐ The demonstration is **structural before experimental**: with a still desktop Mutter does not deliver, `video_a_una()` is not called, **the branch is not reachable** | ⛔ **and the check cannot be «the counter is zero»**: empty and forbidden have the same face. ⇒ **it is done in pairs in the same round** — half still and half moving alternated, `arretrato` **read** in both halves. A round that does not satisfy this **has measured nothing, and must be thrown away instead of interpreted** | §6 |
| **P9** | ⭐ **the comparison of `RCP.md` §4.3 will be made by the program**, not by whoever reads: today the two lines are there but the comparison is manual | ⛔ a level too low **does not give a network error**: **it makes the configuration be refused**, that is a screen that does not start without a red | §5.5 |

---

## §8 · ⛔ What did NOT work

**23 Aug 2026 — three stumbles, and all three of the BENCH, none of the product.**

1. ⛔ **`wc -l < registro.log`: the `<` is opened by `nicfio`'s shell, not by `sudo`.** The log belongs to
   root ⇒ **empty** output ⇒ `riga0 = 0` ⇒ the tally also took in **the earlier sessions**.
   `[M]` The first round counted **413** frames where the server declared **398**. ⚠ It is the
   bad form: not a red, **a plausible number**. ⇒ Cure: the file is opened by `wc`, which runs
   as root.
2. ⛔ **The scene launched with `ssh → sudo → setsid … > $LAV/scena.log`**: same family — the
   redirect towards a root folder was done by `nicfio`, the scene died and **its log was
   empty**, that is *«not started»* without saying why. ⇒ Cure: **a script**,
   `banchi/09-b68-scena.sh` — *a file has no levels of quotes*. ⚠ It is the trap already written
   in `07-b65-datagram.py` for the guardian, paid for again.
3. ⛔⛔ **The positive control itself needed to be controlled.** The first control
   round printed *«the `RICHIEDI_CHIAVE` counter does not move: the bench is blind»* —
   and it accused the bench, while what had not happened was the **stimulus**: in the client
   `--chiave-dopo` lives **inside the branch of `--puntatore-vecchia`**
   (`01-b3-cliente.py`), and without the pointer the request never leaves. ⇒ Cure: the canvas must
   first be **shrunk** (`--adatta 1280x720@3 --puntatore-vecchia 0.3 --chiave-dopo 2`).
   ⭐ **The lesson**: a positive control that gives red has *two* defendants, and the first to look at
   is whether the shot was struck.

⚠ **And one thing that is NOT a defect but must be declared**: the `scena ferma` is a **headless GNOME
without open windows**. A real desktop with a clock in the bar would give a few frames a
minute instead of zero — the shape of the result does not change, the order of magnitude does.
⇒ ⛔ **The final judgement remains with whoever watches, with real work inside.**

**Afternoon — five more, and ⛔ four out of five produced «a plausible number».**
⭐ It is the same shape every time (`LEZIONI.md` §1.9), and that is why it is worth listing them.

4. ⛔ **`pgrep -f 01-b3-cliente.py` finds itself.** The `bash -c` that carries that text in its
   own command line is counted as a session. `[M]` 07:29: *«a session is already
   open (pid 18170)»* while there were **no** sessions. ⇒ Cure: `01-b3-cliente[.]py`
   — the character class never appears in the real line and always appears in the
   wrapper's.
5. ⛔⛔ **«There is a process» is not «there is a session», and it cost four arms out of six.**
   The bench saw alive the client that the previous command had just killed, did not
   open a new one, and thirty seconds later the client really died: from there on **no
   `SPEDITO`**. The bench did not notice. ⇒ Two cures: (a) the session is declared by the **product**
   in its log (*video channel ON* with no detach afterwards); (b) an arm with **zero
   frames** comes out as a **fault**, not as an empty median among the others.
6. ⛔ **`kill -9` after one second is a fault, not a prudence.** The client killed by force does not
   send the `CONGEDO`: the server keeps the session until the QUIC idle timeout expires and the next
   round gets `CONGEDO invece di SESSIONE: 0x0f GIA_ATTIVA_REMOTA`. ⇒ Cure: `TERM`, and **one
   waits**.
7. ⛔⛔ **The `ESC` that opens the door is the same one that closes it.** `ESC` exits GNOME's
   overview — and it is also the key that exits the **browser's full screen**.
   Sent *after* switching the video on, it switched off the video it was supposed to switch on: `[M]` 08:13, the
   «video» point gave **0.202 Mbit/s**, that is the same as «still». ⇒ Cure: the ESC **first**, and the
   page requests full screen **every second** instead of only once.
8. ⛔⛔ **`UID_B` must be passed also to switch off.** `09-b72-video.sh -- spegni` without `UID_B` takes
   the default **1001** and kills «prova»'s Firefox, not «prova2»'s. ⇒ in the four points
   of the 08:11 round **the video stayed on underneath all the others**, and «still» gave
   **25.9 frames/s and 0.235 Mbit/s**: a still desktop that was not still. ⇒ Cure: one switches off
   **and verifies**, and whoever does not die is reported.

⭐⭐ **The lesson of the afternoon, and it is not new**: five faults out of six did not give a red —
they gave **a number that could be written in a table**. ⛔ The two things that found them
all are the same two: **looking at the pixels** (§3.7 was born from an image, not from a counter) and
**demanding that a counter at zero can move**.

---

## §9 · The decisions produced

- **`DECISIONI.md` §2.2**, box of 23 Aug — ✅ **4K is an upper limit, not a
  promise at the floor**: *«non pretendo di averlo su connessioni a 20 mbps»*. ⚠ And the line of
  §3.1 *«good fixed line, 30+ ⇒ aim at the desired»* does not hold even at 30 for **moving** 4K.
  ⛔ A mandatory measurement for this phase comes out of it: **at what bandwidth moving 4K becomes
  usable** — it is declared, not promised. ⛔ And a constraint that is not about bandwidth: the H.264 level
  in force grants at 3840×2160 `[?]` **30.3 frames/s**, not 60 ⇒ **the «60 fps» of the wish list
  is not reachable at 4K even with infinite bandwidth.**
- **`DECISIONI.md` §2.1**, box of 23 Aug — ✅ **480p · 25 fps stays**, but as the **bottom
  of the ladder**: below 25/s on a 20 Mbit/s line it is **a defect**, not a degradation.
- **`DECISIONI.md` §3.1-bis** — ✅ the minimum network is **20 Mbit/s**, declared floor
  (23 Aug 2026). Consequences applied the same day in `SPECIFICHE.md` §8.1,
  `CODER.md` §1-bis, `PIANO.md` phase 9, and `DECISIONI.md` §3.1 marked partly superseded.

### 9.1 ⭐⭐ What the afternoon's measurements put on the table — *to be decided*

⛔ **They are not decisions taken: they are decisions that now have the numbers to be taken.**
`I6` wants whatever changes what is SEEN to stay behind a switch that is off until the user
has looked at it.

> ⚠ **This table was written in the middle of the afternoon, when still *«not one line of the
> product had been touched»*.** ⭐ Then the cures were written — §5 — **all behind a switch that is off**,
> except the two that do not change what is seen. ⛔ **The user's judgement remains the step that is
> missing**, and the table stays because it is the record of the numbers that made it compulsory.

| | the number that makes it compulsory |
|---|---|
| ⛔ **the bandwidth cap must be written** — §0.3 called it «does not exist» | §3.8: a video with grain at full screen asks for **58.7 Mbit/s = 293 %** of the floor, and nobody tells it no |
| ⭐ **but NOT for the real content** | §3.8: the user's desktop at full screen costs **0.204 Mbit/s = 1 %**. ⇒ the cap is for the **hard case**, and a regulator that switched on for normal content would repeat **the error of v1** (*«happy to save»*, §0.2) |
| ⛔ **the regulator CANNOT look at how many pixels change** | §3.8: `pieno` moves **all** the pixels and costs 1.2 Mbit/s; `barra` moves the same pixels with a halftone and costs **21**. Two orders of magnitude for the same surface |
| ⛔ **the cure of `video_sgombra()` is the right lever** | §3.10: `abbandoni §5.1` = `chiavi`, **one to one**, at every bandwidth level. Removing an abandon removes a keyframe |
| ⭐ **and neither hysteresis nor memory of the descent is needed** | §3.10: after the reopening the regime goes back to full in **less than a second**, without aftermath |
| ✅ **the stop with a still scene is NOT a defect** | §3.6: 180 wake-ups, **13 ms** from 0.2 s to 15 s of quiet, tail 2 ms wide. ⇒ §3.1 remains a **literal** violation of I1 that **costs nothing to whoever watches** |
| ⛔ **and there is nothing to optimize in our stretch** | §3.6: of the 13 ms, **10 are waiting for the compositor** and **2.7** are encoding |

---

## §10 · ⛔⛔ THE CONTRADICTIONS — declared, **not smoothed over**

> ⛔ **Two documents of the day say different things.** Here are both positions and
> **what would decide the question**. ⚠ Whoever reads must not choose on trust: they must know
> which measurement is missing.

### 10.1 ⛔ «No bandwidth cap is needed» **against** «it asks for 293 %»

| | the position | what it rests on |
|---|---|---|
| **the morning** | *«On the measured content, at 20 Mbit/s, CQP 26 is just fine, and no bitrate control is needed.»* | `[M]` phase 8: on the user's **real** content, **every frame a keyframe** — the worst regime there is — the median is **24 956 bytes** ⇒ at 20.9 fps that is **4.17 Mbit/s = 21 %** of the floor. **Four times below**, even in the state into which the defect of `video_sgombra()` makes it fall |
| **the afternoon** | ⛔ *«A bitrate control is needed»* | `[M]` §3.8: a film with grain at full screen, 2560×1080, QP 26, **58.668 Mbit/s = 293 %** of the floor |

⭐⭐ **And the two measurements do not contradict each other on the number: they measure two different contents** — and
the morning study had **written it itself**: *«the user's desktop measured in phase 8 does NOT
contain that scene»*. ⇒ The real contradiction is narrower and must be named:

⛔ **What was REFUTED is the study's afternoon estimate**: `[?]` **~19.9 Mbit/s**,
extrapolated from R31 of v1 by rescaling pixels and QP rungs, against **58.7** measured.
**Optimistic by three times.** ⇒ ⭐ Extrapolation from one piece of hardware to another **does not hold**, and this is the
lesson that survives the day more than the conclusion.

⚠ **And the study had written its own falsifier, with the threshold**: *«below 10 Mbit/s ⇒ everything
closes · between 15 and 25 ⇒ a cap is needed, behind the switch that is off · **above 30 ⇒ R31 is
confirmed on our own hardware, and the cap is no longer an option**»*. ⇒ **58.7 is in the third branch**, and it is
for this that cure 5 was written.

⇒ ⭐ **The synthesis that holds both**: *the cap is for the **hard case**, and for real content it
must be inert* — ⛔ **and a regulator that switched on for normal content would repeat
exactly the error of v1** (*«happy to save»*). **It is red no. 1 of prediction P4**,
and the measurement that decides it is already there: the real desktop with the cap on must cost **at least** 0.204
Mbit/s.

### 10.2 ⛔ How much the spiral bites **above** the floor — two positions, and neither is decided

| | the position | what it rests on |
|---|---|---|
| **A** — *«the defect lives BELOW the floor; above, the cure is inert»* | the threshold is **a robustness on transients**, not the cure of the phase | `[M]` **at 15 Mbit/s: 2 keyframes out of 1 019** ⇒ the delta chain was **intact**, and 15 is **below** the floor of 20. And `DECISIONI.md` §3.1-bis says verbatim that below 20 the product *«promises nothing and measures nothing as a requirement»* |
| **B** — *«it bites also above the floor»* | the spiral fires also on a wide line | `[M]` §3.10, the step at 2560×1080 with `barra`: **abandons and keyframes also in the «wide» seconds** — 3↔3 at second 5 (22.1 Mbit/s on the wire) and 1↔1 at second 6 (26.3). ⇒ `video_sgombra()` abandons **even when the line carries it** |

⛔ **It is not chosen here, and the reason is that the two measurements are not comparable**: `barra` is a
synthetic **halftone** gradient that asks for **21 Mbit/s** by itself, that is **a hundred times** the real
desktop (0.204). Content that consumes the whole floor produces a queue even on a wide line;
the content the product exists for does not.

⭐⭐ **WHAT WOULD DECIDE THE QUESTION — one single measurement, and it can be done tomorrow:**

> **`abbandoni §5.1` per second, with the switch OFF, at 20 Mbit/s throttled on the real
> path, on the user's REAL DESKTOP** — not on `barra`, not on `pieno`, not at 2 Mbit/s.

| outcome | ⇒ who is right |
|---|---|
| **≈ 0 abandons/s** | ⭐ **A**: the threshold is a parapet on transients, phase 9 spends its time on the regulator, and cure 2 remains a **prerequisite** |
| **abandons per second at regime** | ⛔ **B**: the defect bites **above** the floor ⇒ the threshold **is not a robustness measure, it is a product cure**, and ⛔ **it changes the priority of the phase** |

⚠ **And the other half of the question is already decided**: `[M]` §3.10 proves that **throttling at a constant 20 Mbit/s
would have shown nothing** — the **step** is needed. ⇒ The measurement above is done **at regime**
to answer A/B, and **with the step** to measure the cure: they are **two rounds, not one**.

---

## §11 · What remains `[?]`

| | where |
|---|---|
| ✅ **the SEGV on the 525 KB frame — CLOSED on the afternoon of 23 Aug**: the cause is proven line by line and ⭐ **the cure is applied**. ⛔ What remains `[?]` is **one thing only: the reproduction**, which was not run ⇒ until the recipe runs, it is a **probable cause with the line**, not a seen cause — and the cure has no proof of having cured | §4 · §4.5 · §4.8 |
| ⏳ ⛔ **the trap is not armed**: no core dump, the log is shared and gets buried, `dmesg` is not collected at shutdown | §4.7 |
| ✅ **the bandwidth cap: which one, and on what quantity — DECIDED on 23 Aug**: `QVBR`, with wire · working point · reservoir derived from the floor, `--tetto-banda-mbit`, **off**. ⛔ What remains `[?]` is the measurement on the test machine (P4) | §5.5 · `codificatore.c:200-340` |
| ⏳ `[?]` **the film with grain cannot be measured beyond 25 s on this machine**: software VP8 decoding at 2560x1080 starves the **client**, which sits on the same machine, and QUIC drops by *idle timeout*. ⇒ the number of §3.8 is good, but a long round wants a client on another machine | §3.8 |
| ✅ the cure of **`video_sgombra()`** — ⭐ **written on 23 Aug**, behind `--sgombra-soglia-ms`, **off**. ⛔ What remains `[?]` is the measurement (P3) and ⛔⛔ **the price, which the user judges**: ~150 ms of slightly old image under congestion | §5.2 · `webtransport.c:2705-2800` |
| ✅ the **audio reorder window** — ⭐ **written on 23 Aug**, without a switch (pure loosening). ⛔ What remains `[?]` is **the verification, and the prescribed bench CANNOT do it**: it measures itself — a bench that runs **the page** is needed | §5.4 · §3.16 · `pagina.html` · `avvia_audio()` |
| ⏳ `[?]` **reordering on Opus**: the measurement is in **5 ms PCM**, with Opus the overtaking threshold is **4 times higher** and the defect bites 4 times less ⇒ the real path is Opus, and on Opus the number is not there. ⚠ And `[?]` whether the Opus decoder tolerates non-monotonic timestamps: **not verified** | §5.4 · P6 |
| ⏳ `[?]` the quality of **`EncSliceLP`** against the full entrypoint at equal bandwidth — **never measured**, and ⚠ **on the home hardware it cannot be done**: the AMD is needed | `PIANO.md:1197` |
| ⏳ `[?]` the **temporal sub-layers** on `EncSliceLP` — `[M]` the driver does not declare `EncRateControlExt` on 7 profiles out of 7 ⇒ *«every abandon costs a keyframe» remains in force* | `RCP.md:1261` |
| ✅ `[R]` **`qualita_corrente` was a one-way ratchet** — ⭐ **cured on 23 Aug** (`risali_qualita()`), behind `--qualita-risale`, **off**. ⛔ What remains `[?]` is the measurement, and the check that decides is **THRASHING** (P5) | §5.3 · `codificatore.c` |
| ⏳ ⛔ **the rate regulator — designed, NOT written**: it is the work that remains, and ⛔ **the order is mandatory** (first the queue threshold, or `arretrato` is zero by construction) | §6 |
| ⏳ ⛔ **the descent log** (`🔻`/`🔺 RITMO`) — designed, not applied. And ⛔ **the floor (480p·25 and 20 Mbit/s) does not exist in the code yet** | §7.1 · §7.2 |
| ⏳ `[?]` **the congestion algorithm was never chosen**: ngtcp2's CUBIC is taken. ⚠ On WiFi CUBIC reads a **radio** loss as congestion; BBR works on bottleneck bandwidth and `min_rtt`. ⛔ **A separate experiment, behind its own switch** — not two variables in the same bench | §6.3 |
| ⏳ `[R]` the **comparison `livello_flusso` ≤ `video.livello`**: the two lines are now there, ⛔ **but the comparison is made by whoever reads, not by the program** | §5.5 · P9 |
| ⏳ `[?]` the value of **`CRF_PASSO`** (9 is *sufficient, not right*); the effective ladder is **26 → 35 → 44 → 51** | `codificatore.c` · `RICODIFICHE_MASSIME` |
| ⏳ **`AUDIO_CUSCINO_MS = 250`** not lowered: it must cover **the arrival jitter, which nobody has measured**. ⚠ And **it has nothing to do with bandwidth**: it is a thread problem | `pagina.html` · `AUDIO_CUSCINO_MS()` |
| ⏳ **QUIC migration** from WiFi to mobile network — *«the best reason why QUIC was chosen»* | `PIANO.md:1437` |
| ⏳ the **audio datagram on a non-local network**, never measured (probe `banchi/07-b40`) | `RCP.md:1329` |
| ✅ *closed on 23 Aug* — **§2.1, the minimum stays 480p · 25 fps**: *«480p/25fps è il pavimento»*. ⛔ The reason changes: it is **the bottom of the degradation ladder**, no longer the level a poor line forces ⇒ **a rate below 25 on a 20 Mbit/s line is a DEFECT** | `DECISIONI.md` §2.1 |
| ❓ the **network budget** beside the GPU one: ten sessions × 20 Mbit/s = **200 Mbit/s** on the wire. To be measured in phase 10 | `DECISIONI.md` §4.6 |
| ⚠ the **declared H.264 level** is `avc1.640032` (High **5.0**), but beyond 40 Mbit/s **5.1** is needed: a level too low gives no error, **it makes the configuration be refused** | `SPECIFICHE.md:1087` |

---

## §12 · The user's judgement

⏳ *The phase has not reached the judgement.*

⛔ **And there are two precise things that wait for him**, listed in **S.5** with the price beside them: the
**queue threshold** (`--sgombra-soglia-ms`) and the **bandwidth cap** (`--tetto-banda-mbit`). ⚠ Both
change what is SEEN, both are born off, and ⛔ **which is the lesser evil is not decided
by a measurement**: it is exactly the lesson of the reset of phase 10 of v1.

---

# §13 · ⭐⭐ THE SECOND ROUND OF MEASUREMENTS — *23 Aug 2026, afternoon-evening*

> ⛔ **This section fills up as we go**, one number at a time with the time beside it.
> The predictions are those of **§7.4 (P1…P9)** and of summary **S.5**: here, beside every
> number, there is **the expected**.

## 13.0 ⛔ WHAT CODE THESE NUMBERS COME FROM — the `md5`s, and why they stand at the top

⛔ **The first fact of the evening is that the 7920 tree was OLD.** `/media/REMOTIX/src/09c-src`
carried a `webtransport.c` of 23 Aug **09:23** (`md5 958170e2…`) — that is **without the rate
regulator** (cure 6): missing were `video_ritmo_scesi`, `ritmo_frena()`, `ritmo_ciclo()`,
`wt_ritmo_adattivo()`, **506 lines of diff**. ⇒ Every measurement taken on that binary with
`--ritmo-adattivo` would have given *«zero descents»* **because the option did not exist**, not because the
regulator did not fire. ⚠ It is exactly defect D5 of this phase, with another face.

⭐ **Both trees redone from the committed code `f90eb21`**, at **15:05-15:20 local**:

| tree | `webtransport.c` | what it is |
|---|---|---|
| `/media/REMOTIX/src/09c-src` | `md5 4785abf10e50bf4d86ce638a21bd685b` | ⭐ **the CURED** — identical byte for byte to `src/webtransport.c` of `f90eb21` |
| `/media/REMOTIX/src/09c-mal-src` | `md5 69e2d57fac73f48ce9e0ef6c0e628add` | ⛔ **the SICK** — the only difference is `coda_uccidi()` in place of `coda_consegna()` (`:6421`), that is the defect of 08:28:09 put back on purpose: **it is the positive control** |

The other sources are identical in the two trees and to the commit:
`codificatore.c md5 5a29b80787042b0c6511c74d159c1bd0` · `main.c md5 2aa34655c19e20b5f0acf35c9c0af484` ·
`pagina.html md5 e010d615f10643d5c6e2a2c01ae5ff25`.

⚠ **And `--pagina` now points to ITS OWN tree**: the server started in the middle of the afternoon served
`/media/REMOTIX/src/09-src/src/pagina.html`, that is the page **before** cure 4.

## 13.0-bis ⛔ TWO STUMBLES OF THE REBUILD — *15:05-15:20*, and the first is **the trap of this phase**

1. ⛔⛔ **`enter.sh` stayed hung for 13 minutes on `sudo`, and the cause is not what it seems.**
   The script gave the password **once** (`printf 'nicfio\n' | sudo -S -v`) and then called
   `bash /media/REMOTIX/enter.sh --root '…'`, counting on the credential being cached.
   ⛔ **It is not**: `enter.sh` does its `sudo -n true`, which **fails**, and falls back on
   `sudo -v -S -p 'Password sudo: '` — which starts reading from its own standard input, that is from
   an `ssh` pipe **open and empty**. ⇒ process in `do_wait`, **zero log lines, zero
   children, load 0.08**: the face of a slow compiler.
   ⭐ **Why the credential is not inherited**: `sudo` by default keeps the mark **per terminal**
   (`timestamp_type=tty`), and **without a tty it falls back on the parent process**. Two sibling processes are
   two different parents ⇒ two different caches. ⛔ **The form that works is the one written in `enter.sh`
   itself, line 17**: `printf '%s\n' "$PASSWORD" | bash /media/REMOTIX/enter.sh "…"` — the password must be
   given **to `enter.sh`**, not to an earlier `sudo`.
   ⇒ Redone this way, **the two trees built in 7 seconds each**, `make -j` and all
   (`13:18:16 → 13:18:30` UTC), with `OK make e' uscito 0` and the twelve marks inside the binary.
2. ⚠ **The `tar` of the code is not enough to run a bench.** `src` + `banchi/rcp` builds, but
   the test session is opened by `banchi/01-b3-cliente.py`, which was not there ⇒
   `SESSIONE MORTA prima di aprirsi — python3: can't open file …`. ⭐ An **immediate and
   honest** red, in 20 seconds: the bench said *which* file was missing. ⇒ copied all of `banchi/*.py`
   `*.sh` into both trees (`01-b3-cliente.py md5 13e68d19ed44298b7926cded53affdda`,
   **the same** as the two trees of the morning: the yardstick has not changed).

## 13.1 ⛔⭐⭐ P1 — THE MEMORY CURE: the two binaries paired

⛔ **The shape of the proof**, and it is not negotiable: *«the cured one did not die»* is not a result — it has
the same face as a stimulus that does not stimulate. ⇒ **same port, same working folder,
same scene, same loss**, and the only variable is the line `webtransport.c` · `wt_scrivi()`.

⭐ **The glibc trap is verified in the LIVE process**, not in the script:
`MALLOC_MMAP_THRESHOLD_=32768 MALLOC_PERTURB_=165` read from `/proc/PID/environ`.

### 13.1.1 ⛔⭐⭐⭐ THE SICK ONE DIED — *23 Aug 2026, 13:21:11 UTC*, and **the case is closed without margin**

`[M]` **SICK arm** (`09c-mal-src`, `remotix md5 53a7e3be82f2a1f43afe6ead4398012d`), scene
**film with grain at full screen, 2560×1080**, `prova2` session, glibc trap armed and
verified in the live process.

| | expected (**P1**) | `[M]` measured |
|---|---|---|
| does it die? | ⛔ **yes, or the diagnosis of §4 is wrong** | ⭐ **YES**, at **13:21:11** |
| the signal | `SEGV`, `error 4` | ⭐ `segfault at 7fc39818e4ca ip 00007fc39f338b49 **error 4** in libc.so.6[**162b49**…]` |
| where | always in `__memmove_avx_unaligned_erms` | ⭐ **the very same offset `162b49`** as the crash of 08:28:10 |
| the core | §4.7 point 1 wanted it **absolute** | ⭐ **it is there**: `core.remotix.86418…`, **48 529 408 bytes** |

⭐⭐⭐ **And the core gave the stack, that is what §4.8 declared `[?]` — «the retransmission was not
seen with the eyes».** Now it is:

```
#0  __memmove_avx_unaligned_erms          ← libc, rip 0x…b49
#1  ngtcp2_cpymem                          ← ngtcp2_pkt.c:1619
#2  ngtcp2_pkt_encode_stream_frame
#3  ngtcp2_ppe_encode_frame
#4  conn_write_pkt
#5  ngtcp2_conn_write_vmsg
#6  ngtcp2_conn_writev_stream_versioned
#7  wt_scrivi (…) at webtransport.c:6314   ← NOSTRO
#9  scrivi_connessione at trasporto.c:422
#12 main at main.c:1395
```

⛔ **It is the chain written by hand in §4.8, line by line, now read from the core.** ⇒ the `[?]` of §4.8
**is closed**: the cause is no longer *«probable with the line»*, it is **seen**.

⭐⭐ **And there is more — and it changes the recipe.** The last line of the log, 300 ms before the death:

```
13:21:10.776 rcp  fotogramma 27 SPEDITO: delta 0x0302, codec 1, 2560x1080, 516782 byte di dati, stream 119, FIN
```

⛔ **`516 782` bytes — the twin of the `525 298` of 08:28:09.** ⇒ **one large frame is enough: the
loss is not needed.** The server died **at frame 27, in 13 seconds of session**, and
⛔ **`netem loss 5%` had not been applied yet** (it arrives 13 s later, at 13:21:24). ⚠ Recipe
**B** of §4.5 asked for real loss; **A** asked for the frozen client: `[M]`
**neither is needed**. With `MALLOC_MMAP_THRESHOLD_=32768` **half a megabyte of
delta and clean loopback** are enough — because a 516 KB frame does not fit in a packet and ngtcp2
rereads **our pointer** at the next packet, which in the sick one is already `munmap`-ed.
⇒ **The shortest recipe of all, and the harshest**: 27 frames against **45 005**.

### 13.1.2 ⭐⭐⭐ THE CURED ONE HELD — *13:22:35 → 13:25:03*, and the stimulus was **harder**

`[M]` **CURED arm** (`09c-src`, `remotix md5 162d2d105cbe930e7921a7041053f5e7`), **identical in
everything** to the sick arm: same port 7920, same folder `tmp/09c`, same `prova2`
session at 2560×1080, same film with grain, same glibc trap verified in the live process.

| | SICK `09c-mal-src` | ⭐ CURED `09c-src` |
|---|---|---|
| frames sent | ⛔ **27**, then dead | ⭐ **1 463** |
| median size | — | **302 984** bytes |
| **maximum size** | 516 782 (the last) | ⭐⭐ **537 063** bytes — ⛔ **larger than the 525 298 that had killed it this morning** |
| frames above 32 KiB in the first 6 s | 0 read (dead before) | ⭐ **173 out of 173** — that is **every** frame went through the trap |
| `netem loss 5%` | ⛔ **it was not even needed** | ⭐ **120 whole s** with the loss on it |
| outcome | ⛔ `SEGV` at 13:21:11 | ⭐ **ALIVE**, no core, no line in `dmesg` |

⛔⛔ **And the stimulus of the cured one was HARSHER than the one that killed the sick one**, not less: more
frames (1 463 against 27), larger (up to 537 063 bytes), and on top of that **with 5 %
loss**. ⇒ *«the cured one did not die»* here does **not** have the face of a stimulus that does not stimulate.

### 13.1.3 ⭐ THE QUANTITY THAT TELLS WHETHER THE CURE LEAKS MEMORY — and it does not leak

The closing line, `13:25:35.869` (`webtransport.c` · `wt_libera()`):

```
⭐ FASE 9, i byte TENUTI per la ritrasmissione (contratto di ngtcp2_conn_writev_stream):
   punta 537063 byte, residuo alla chiusura 31, e 1185696 byte ancora da spedire in coda
```

| quantity | expected | `[M]` |
|---|---|---|
| `byte_in_volo_max` (the peak) | ⭐ **oscillates**, does not grow | **537 063** bytes = **exactly one frame**, the largest of the session. ⛔ In 1 463 frames **~443 MB** passed: if it held without freeing, the peak would be that. ⇒ **the cure frees** |
| residue at closing | **zero** | ⚠ **31 bytes** — not zero, but **31**: the tail of a stream not yet acknowledged at the instant of a brutal tear (the client killed, with 5 % loss on it). ⛔ **I declare it instead of rounding it**: it is green, not full green |
| bytes still in the queue | — | 1 185 696 — what had not left yet when the client disappeared |

⭐ **And the same closing line carries the number P2 needs**, with the switch **off**:

```
⭐ FASE 9, la soglia della coda video: spenta (I6) (0 ms) — delta TENUTI 0,
   abbandonati per soglia 594, e NON ACCETTATI per credito mancato 0
```

⇒ ⛔ **594 deltas abandoned** in 178 s of hard film with 5 % loss, and **`credito mancato` = 0**:
the debt does **not** come from cause 4 of §2.3.

### 13.1.4 ⛔ VERDICT ON P1 — **the prediction held, and more than it asked**

| | |
|---|---|
| **the crash reproduces** | ⭐ **YES** — and with a recipe **shorter** than all three of §4.5 |
| **the cure holds** | ⭐ **YES**, paired, on the same hardware and with the harder stimulus |
| **the cause is seen, not deduced** | ⭐ **YES** — the stack from the core closes the `[?]` of §4.8 |
| **memory is not lost** | ⭐ **YES** — the peak is worth one frame out of ~443 MB passed |

⚠ **And the two bench defects that must be told** (neither changes the outcome, both change the
bench):
1. `09-b73-memoria.py` **reads the `byte TENUTI` line too early** — it looks for it 3 s after the death of the
   client, and the server writes it when it tears down the WebTransport session. ⇒ the bench printed
   *«(no «byte TENUTI» line)»* while the line **was there**, written 3 seconds later. ⛔ It is the bad
   form: **an absence that looks like a result**;
2. `b71.pulizia()` **does not look at Firefox**. Its `pgrep` covers `04-b30-scena`, `01-b3-cliente`,
   `b70-ritmo`, `b65-datagram` — ⛔ **not `firefox`**. ⇒ for both arms an orphan
   Firefox of bench `09-b74` stayed alive in the `prova` session (uid 1001), and the bench said
   *«other benches alive: none»*. ⚠ It does not touch the outcome (it is the **same** dirt in both arms, and it
   was on another session), but it is **precisely the defect that has already produced plausible and wrong
   numbers today**.

### 13.1.5 ⭐⭐ THE CRASH REPRODUCES **TWO TIMES OUT OF TWO** — and the third stumble of the bench

⛔ **The core of 13.1.1 is no longer there, and I deleted it without meaning to.** `09-b73-memoria.py`
starts every arm with `rm -f registro.log core.*` — it serves not to mix the two rounds, ⛔ **but
it also throws away the proof of the previous arm.** ⇒ Running the *cured* arm I destroyed the core
of the *sick* one. ⭐ The **stack** had already been read and is here above: what was lost is the file.

⭐⭐ **And redoing it cost two minutes, with a gain**: the crash reproduced **a second
time, identical**.

| | first round | ⭐ second round |
|---|---|---|
| time | **13:21:11** | **14:03:24** |
| signal | `segfault … error 4 in libc.so.6[**162b49**…]` | `segfault … error 4 in libc.so.6[**162b49**…]` |
| time to die | **0.3 s** from the start of the wait | **0.3 s** |
| core | (deleted) | ⭐ `core.remotix.110832.1787493803`, **48 525 312 bytes** |

⇒ ⛔ **Two out of two, same offset in libc, same error code.** It is not a rare case of
1 in 45 005: **with the trap armed it is deterministic.**

⚠ **The correction to make to the bench** (I did not make it: `src/` and the benches are not touched tonight):
`09-b73` must delete **only the log**, and put the cores in a folder per arm.

## 13.2 ⭐⭐ P2/P3 — THE QUEUE THRESHOLD, on the step, paired

**The round**: 8 s wide → **3 s at 10 Mbit/s** → 17 s wide, scene `barra`, **1920×1080**, `prova2`
session, `netem` only on 7920 on `lo` with the guardian armed. ⛔ glibc trap **off**
(`MALLOC=no`) in both arms: `MALLOC_MMAP_THRESHOLD_` is slow, and leaving it on
would have measured **it** instead of the threshold.

### 13.2.1 `[M]` THE ARM WITH THE SWITCH OFF — *13:27:20 → 13:28:0x*, and it serves as the yardstick

`⭐ FASE 9, la soglia della coda video: **spenta (I6) (0 ms)**` — read from the server's log.

| s | frames | keyframes | abandons §5.1 | wire Mbit/s | phase |
|---|---|---|---|---|---|
| 5-7 | 40-41 | **0** | **0** | 21.1-21.5 | wide |
| **8** | 21 | ⛔ **6** | ⛔ **6** | 9.87 | **narrow** |
| **9** | 25 | ⛔ **6** | ⛔ **6** | 9.14 | **narrow** |
| **10** | 22 | ⛔ **6** | ⛔ **7** | 9.87 | **narrow** |
| 11 | 28 | 4 | 3 | 16.87 | (return) |
| 12-27 | 39-42 | **0** | **0** | 20.4-23.0 | wide |

⭐ **`abbandoni` = `chiavi`, one to one, at every second** (6↔6, 6↔6, 7↔6): §3.10 reproduces
**identically**, and it is the mechanism of the spiral seen live.
⭐ **And the return is immediate**: from second 12 it is already at 40/s with **zero** keyframes — no
hysteresis, no aftermath in 16 s.
⚠ **A number that does NOT match the cited «before»**: this morning's `[M]` gave **13-14 fps** in
seconds 8-10; here they are **21-25**. ⛔ I declare it instead of smoothing it — the yardstick of the *before* and that
of now are not the same round, and **the comparison that holds is the paired one below**, taken
half an hour apart on the same port, same scene, same canvas, same binary.

### 13.2.2 ⛔⭐ THE ARM WITH `--sgombra-soglia-ms 100` — *13:28:26 → 13:29:1x*: **the mechanism runs, the promised effect does NOT arrive**

`⭐ FASE 9, soglia della coda video (§5.1): **100 ms** … Impostata da: main.c, dalla riga di comando`
— read from the server's log, not deduced from the command.

| s | frames **off → 100 ms** | keyframes **off → 100** | abandons **off → 100** |
|---|---|---|---|
| 5-7 (wide) | 39-41 → **39-40** | 0 → **0** | 0 → **0** |
| **8** | 21 → **29** | 6 → **4** | 6 → **6** |
| **9** | 25 → **26** | 6 → **5** | 6 → ⛔ **9** |
| **10** | 22 → **21** | 6 → **5** | 7 → **5** |
| 11 (return) | 28 → **34** | 4 → **3** | 3 → **3** |
| 12-27 (wide) | 39-42 → **39-42** | 0 → **0** | 0 → **0** |

| the prediction (**P3** and S.5) | `[M]` | outcome |
|---|---|---|
| fps in sec 8-10 **≥ 25** | **29 · 26 · 21** | ⚠ **two out of three** |
| keyframes/s **≤ 2** | **4 · 5 · 5** | ⛔ **NO** |
| abandons/s **≤ 2** | **6 · 9 · 5** | ⛔ **NO** — and at second 9 they **rose** |
| seconds 7 and 12 **identical** to the switch off | 40/39 and 40/39, **0 keyframes** in all four | ⭐ **YES — the cure is INERT on the wide line** |
| return **≥ 32/s** within one second | sec 11 **34/s**, sec 12 **39/s** | ⭐ **YES**, and better than the arm off (28) |
| ⭐ **`arretrato` must rise to 2-3** (today zero by construction) | **2 (14 times) · 3 (19) · 4 (6)** | ⭐⭐ **YES, and it reaches 4** |

⭐⭐ **And the mechanism can be seen working, line by line**: **17 crossings ABOVE** the threshold and
**17 returns BELOW** in the 3 seconds of squeeze, with the lines saying by themselves what they did:

```
⛔ la coda del video passa SOPRA la soglia (135475 byte = 114 ms, soglia 100 ms,
   dalla banda misurata (cwnd/rtt)), arretrato 2 delta: da qui i piu' vecchi si abbandonano
⭐ la coda del video torna SOTTO la soglia (100369 byte = 84 ms, soglia 100 ms):
   i 2 delta arretrati si TENGONO — §5.1 dice PUO', non DEVE
```

### 13.2.3 ⛔⛔ THE DIAGNOSIS, AND THE CURE MUST BE TUNED IN THE DIRECTION **OPPOSITE** TO THE PREDICTED ONE

⛔ **P3 had already written the remedy for this case, and wrote it backwards**: *«fps do not
rise ⇒ threshold too high, **go down to 50**»*. ⭐ **The bytes say go up.** Here is why — the
**17** values at which the queue crossed the threshold, in ms:

```
101 · 103 · 106 · 109 · 113 · 114 · 116 · 117 · 117 · 120 · 125 · 126 · 126 · 128 · 134 · 135 · 138
```

⛔ **They are ALL between 101 and 138.** During the squeeze the video queue **oscillates right around
100 ms**: the threshold is planted **in the middle of the oscillation**, and every half breath makes it
cross. ⇒ The cure spends half the time **keeping** and half **abandoning**, and the total
of abandons stays **23 against 24** — that is **no difference**.
⛔ **With the threshold at 50 ms the crossing would always be in progress and the cure would go back to
pure `sgombra`**, that is worse. ⇒ **the right direction is to RAISE it**, and the prediction to falsify
now is: *at 200 ms the crossings collapse, keyframes and abandons with them*.

### 13.2.4 ⭐⭐⭐ THE PROOF THAT DECIDES — *at 200 ms the crossings do NOT collapse: they move*

`[M]` 13:30. Same round, `--sgombra-soglia-ms 200`. The **14** values at which the queue crossed:

```
204 · 206 · 209 · 211 · 211 · 212 · 219 · 221 · 222 · 222 · 224 · 225 · 227 · 236 ms
```

⛔⛔ **Again all just ABOVE the threshold, as at 100 they were all between 101 and 138.**

⭐⭐⭐ **And this is the discovery of the evening, and it changes the way of reading cure 2**: the threshold
**is not a filter, it is the WORKING POINT of the queue.** `video_sgombra()` abandons as soon as the
queue exceeds the threshold ⇒ **the queue can never go much above it**, whatever number is chosen: it
settles just beyond. ⇒ The number of abandons **is not decided by the threshold**: it is decided by the gap
between how much goes in and how much comes out. The threshold decides **how deep it accumulates before
abandoning**, that is **how much delay is paid**.

| | off | **100 ms** | **200 ms** |
|---|---|---|---|
| frames in the 3 s | 68 | 76 | **79** |
| ⛔ **keyframes** in the 3 s | **18** | 14 | **11** |
| abandons §5.1, whole round | 24 | 23 | **18** |
| kbytes delivered in the 3 s | 3 896 | 4 300 | **4 476** (+15 %) |
| ⚠ **`arretrato`** (the price) | 0-1 by construction | 2 (14×) · 3 (19×) · **4** (6×) | 3 · **4** (15×) · **5** (10×) · **6** (6×) |
| ⚠ **the delay paid** | — | 101-138 ms | ⛔ **204-236 ms** |

⭐ **There is an improvement, and it is monotonic**: the higher the threshold, the more frames and the fewer keyframes.
⛔ **But it is FAR from what P3 promised** — *keyframes ≤ 2/s* came out **3-5/s**, and *abandons
≤ 2/s* came out **5-6/s**. ⇒ **P3 is REFUTED on the two numbers that counted**, and confirmed on the
side ones (inertia on the wide line, return under one second).

⛔⛔ **And the price for the user must be corrected upwards.** S.5 declared *«up to ~150 ms of
delay for a moment (~205 ms from gesture to pixel)»*. `[M]` at threshold 100 the queue reaches **138 ms**
(⇒ ~193 ms of loop) and **at threshold 200 it reaches 236 ms** (⇒ **~291 ms of loop**). ⚠ The estimate of
S.5 was **right for 100 ms and wrong for any more generous tuning**, and the more
generous tuning is precisely the one that gives the best image. ⛔ **It is the compromise he decides, and now
he has the two numbers.**

⭐ **And one thing the threshold did well, and it is its prerequisite**: it brought `arretrato` from
**0-1 by construction** to **2-6**. ⇒ `WT_RITMO_POSTI = 2` is **exceeded continuously**, and the
rate regulator — which without the threshold would never fire — now **can** fire.

## 13.3 ⭐⭐⭐ P7 — THE RATE REGULATOR: **the spiral switches off, and the two counters go to ZERO**

**The round**: identical to the three above — 8 s wide → 3 s at 10 Mbit/s → 17 s wide, `barra`,
1920×1080 — with `--sgombra-soglia-ms 100 --ritmo-adattivo`. The two startup lines, **verbatim**:

```
⭐ FASE 9, soglia della coda video (§5.1): 100 ms … Impostata da: main.c, dalla riga di comando
⭐ FASE 9: il regolatore del ritmo e' ACCESO (`--ritmo-adattivo`): un fotogramma NON parte
   quando 2 delta in volo hanno ancora byte nella mia coda d'uscita
```

### 13.3.1 ⛔⭐⭐⭐ THE FOUR ARMS, SIDE BY SIDE — *and the fourth does not resemble the other three*

| in the 3 s of squeeze | off | threshold 100 | threshold 200 | ⭐⭐ **100 + rate** |
|---|---|---|---|---|
| frames/s | 21 · 25 · 22 | 29 · 26 · 21 | 31 · 23 · 25 | 26 · 23 · **20** |
| ⛔ **KEYFRAMES/s** | **6 · 6 · 6** | 4 · 5 · 5 | 3 · 5 · 3 | ⭐⭐⭐ **0 · 0 · 0** |
| ⛔ **abandons §5.1/s** | **6 · 6 · 7** | 6 · 9 · 5 | 5 · 6 · 5 | ⭐⭐⭐ **0 · 0 · 0** |
| keyframes in the whole round | 18 | 14 | 11 | ⭐ **0** |
| abandons in the whole round | 24 | 23 | 18 | ⭐ **0** |
| on the wide line (sec 0-7, 12-28) | 39-42 fps, 0 keyframes | same | same | ⭐ **same: 37-41 fps, 0 keyframes** |

⛔⛔ **The spiral was not attenuated: it was SWITCHED OFF.** Zero keyframes and zero abandons in the whole
round — and not because the threshold worked better, ⭐ **but because it did not have to work at all**:
`passa SOPRA la soglia` **0 times**, `torna SOTTO` **0 times**. The regulator keeps `arretrato`
nailed at **2**, and the queue never reaches the 100 ms that would wake `video_sgombra()`.
⇒ **The two cures do not add up: 6 makes 2 useless on the step.**

### 13.3.2 ⭐⭐ THE CHECK OF §6.5, the one *«that invalidates the whole bench»* — **passed**

`LEZIONI.md` §1.9: a counter at zero on a branch never travelled proves nothing. The line of
`ritmo_ciclo()` answers, **one per second**:

| time | `arretrato` READ | maximum | descents in the second | in total |
|---|---|---|---|---|
| 13:32:19-27 (wide) | ⭐ **36-42 times/s** | **0** | **0** | 0 |
| **13:32:28** | 40 | **2** | ⛔ **13** | 13 |
| **13:32:29** | 40 | **2** | ⛔ **17** | 30 |
| **13:32:30** | 38 | **2** | ⛔ **17** | 47 |
| **13:32:31** (return) | 38 | **2** | 10 | **57** |
| 13:32:32-48 (wide) | ⭐ **38-42 times/s** | **0** | **0** | ⭐ **57, and it stays 57** |

⭐⭐ **The reads are there — 36-42 per second — and they are worth ZERO.** ⇒ It is not *«a loop never
travelled»* (red **d** of `ritmo_frena()`): it is **travelled 40 times a second, and the answer is
«there is nothing to do»**. It is exactly the behaviour S.5 called *parapet*.

### 13.3.3 ⭐ TWO LINES PER EPISODE, not one per frame — and the RISALE arrives

`[M]` **5 descents and 5 climb-backs**, 10 lines in all for **57** frames held back (the defect of the
30.8 GB of log does not repeat):

| episode | duration | frames held back | `cwnd_left` at the descent |
|---|---|---|---|
| 1 | 158 ms | 4 | **0** |
| 2 | 841 ms | 16 | 51 466 |
| 3 | 607 ms | 10 | 12 117 |
| 4 | ⚠ **1 385 ms** | 25 | **0** |
| 5 | 68 ms | 2 | 264 318 |

⭐ **The RISALE after the line comes back is within the second**: episode 4 started at
`13:32:30.071`, **inside** the squeeze, and closed at `13:32:31.455` — the line had reopened
at `13:32:31.1`, so **355 ms later**. ⚠ *«lasted 1 385 ms»* does **not** refute *«RISALE within 1 s»*:
the right stopwatch starts from the return of the line, not from the start of the episode.

⭐ **And red (b) of `ritmo_frena()` — the most important — did NOT fall**: `cwnd_left` is **0** in
two descents out of five and small in a third ⇒ **it is the line that brakes, not the browser's
window**. ⚠ The only descent with a wide `cwnd_left` (264 318) is the **fifth**, the 68 ms one,
fired when the line had already reopened and `cwnd` was growing back: consistent.

### 13.3.4 ⚠ THE PRICE, measured — **and the number to bring to him**

⛔ The price is the one declared in S.5, and now it has a figure: in the 3 seconds of squeeze one sees
**20-26 frames/s instead of 21-25** — that is **practically the same**, but **all made of
deltas**, without the 18 keyframes. ⭐ In bytes, 100+rate delivers in the 3 s **4 349 kbytes** against the
**3 896** of the arm off: **more image, not less**.

⚠ **And the only number that approaches a limit**: at second 10 it goes down to **20 fps**, below the
25 that `DECISIONI.md` §2.1 calls the floor. ⛔ **It is not the defect S.5 declared**: that line
speaks of *«below 25/s on a 20 Mbit/s line»*, and here the line is **10 Mbit/s**, that is **half the
floor**. ⇒ It must be looked at again on the day one measures at 20.

## 13.4 ⭐⭐⭐ P4 — THE BANDWIDTH CAP: **the two reds that would close the cure did NOT fall**

**The round**: five scenes at **2560×1080**, 30 s each, `prova2` session, `tc` never touched.
⛔ **And the order of the scenes is part of the measurement, and it was corrected along the way** — see 13.4.3.

### 13.4.1 `[M]` THE TEN NUMBERS, paired — *cap off 13:38, cap 20 at 13:41*

| scene | ⛔ **cap OFF** | ⭐ **`--tetto-banda-mbit 20`** | |
|---|---|---|---|
| **still** (no scene) | 0 fps · **0.000** Mbit/s · wire **2.427** | 0 fps · **0.000** · wire **2.427** | ⭐ identical to the third decimal |
| **flat colour** (`pieno`) | 41.10 fps · **1.151** Mbit/s | 41.23 fps · **1.219** | ⚠ **+5.9 %** |
| ⛔⛔ **REAL desktop** (`video`) | 23.13 fps · **0.208** = **1.0 %** | 23.13 fps · ⭐⭐ **0.249** = **1.2 %** | ⭐⭐⭐ **RISES by 19.7 %, does NOT go down** |
| ⛔⛔ **halftone gradient** (`barra`) | 34.67 fps · **21.183** = **105.9 %** | ⭐⭐ **40.70** fps · ⭐⭐⭐ **8.287** = **41.4 %** | ⭐ **the driver DID obey** |
| **film with grain** | 23.17 fps · **54.302** = 271.5 % · wire **58.414 = 292.1 %** | 23.30 fps · ⭐ **4.794** = **24.0 %** · wire **7.419 = 37.1 %** | ⭐ from **293 %** to **37 %** |

⭐ **And the yardstick is good**: the five numbers with the cap off reproduce §3.8 within 1-2 %
(0.208 against 0.204 · 1.151 against 1.179 · 21.183 against 21.36 · 58.414 against 58.668).

### 13.4.2 ⛔⛔ THE TWO REDS THAT WOULD CLOSE THE CURE, one by one

| the red of **P4** | what would have happened | `[M]` |
|---|---|---|
| ⭐⭐ **the real desktop costs LESS than 0.204** ⇒ *«the cap saves where it must not, it is v1 repeating itself, and this cure is thrown away»* | 0.208 → something below 0.204 | ⭐⭐⭐ **it did NOT fall**: 0.208 → **0.249**, that is **+19.7 %**. ⚠ It is the **price of QVBR** already predicted (`[M]` on the laptop: *«it spends 13 % more than CQP with a still scene»*), measured here at **19.7 %** — ⇒ **the cure LIVES** |
| ⭐⭐ **the halftone stays above 20** ⇒ *«the driver did not obey, and only the third witness catches it»* | 21.18 → still ≥ 20 | ⭐⭐⭐ **it did NOT fall**: **8.287** Mbit/s, that is **39 %** of before |

⚠ **And there is a gap from the prediction that must be told, and it is in the direction opposite to a red**: P4 said
*«halftone 11-16 · grain 11-16, and NEVER above 16»*. `[M]` out came **8.287** and **4.794** —
⛔ **below the range, not above.** ⇒ The cap **squeezes more than predicted**: the wire is
**16 000 kbit/s** and the hard case uses **24-62 %** of it. ⚠ It means that on the hard case the image is
uglier than the cap would require: `[?]` **to be tuned**, not a defect — and **it is not decided by
a measurement, it is decided by the eye**.

⭐ **And nobody pays for the frames, on the contrary**: on the halftone the cap on delivers **40.70/s
against 34.67** — because smaller frames get out faster.

### 13.4.3 ⭐⭐ THE THREE WITNESSES, all three read — *and they are the lines the product writes by itself*

| # | the line, verbatim |
|---|---|
| **1** · the driver | `controllo del bitrate su «/dev/dri/renderD128» (Intel iHD driver … 25.2.3), profilo 17, EncSliceLP: il driver DICHIARA [CBR\|VBR\|VCM\|CQP\|MB\|QVBR\|TCBRC] (0x149e) · chiesto QVBR (0x400) · c'e'` |
| **2** · the context | `PARAMETRI IN VIGORE (fase 9) … tetto di banda ACCESO (pavimento 20 Mbit/s)` + `codificatore 1 APERTO e TENUTO VIVO … 2560x1080 a 60/s` |
| **3** ⭐⭐ · **the BYTES** | `banda del video: 5581 kbit/s su 10001 ms — 283 fotogrammi …, modo QVBR · TETTO ACCESO: filo 16000 kbit/s, **ne usa il 34 %**` — one line every 10 s |

⭐ **The third is the one that decides, and it says the cap is engaged**: in the ten intervals read the
consumption goes from **1 %** (still desktop) to **62 %** of the wire, and **never exceeds it**.

### 13.4.4 ⛔ THE BENCH DEFECT I FOUND AND CORRECTED — *and it would have given «a plausible number»*

`09-b72-banda.py` `scena()`: when the next point is **not** a video, **it does not switch off the Firefox of the
previous point**. ⇒ With my first order (`ferma,video,pieno,barra,video-grana`) the `pieno` point was
measured **with the film still alive underneath**. ⛔ It is the family of defects of §8, fourth time today.
⭐ **Everything redone with the video scenes AT THE END** (`ferma,pieno,barra,video,video-grana`): between two
videos `09-b72-video.sh` takes care of it, doing `pkill`.
⚠ **And the outcome of the check must be told**: the contaminated `pieno` had given **1.162** Mbit/s, the
clean one **1.151** — that is **the same number**. ⇒ In *this* case the contamination did not bite
(the scene's window covers the film and Mutter does not deliver what is hidden). ⛔ **But the good
measurement is the one with the right order**, and the bench must be corrected: a defect that does not bite today bites
tomorrow.

## 13.5 ⛔⛔⛔ THE FACT THAT PUTS §3.8, §10.1 AND THE WHOLE BILL BACK INTO QUESTION: **HEVC was being measured**

⭐ Found **by reading the cap's log**, not by looking for it. The line nobody had looked at:

```
13:41:53.152 rcp   negoziato video.codec=hevc video.profondita=8 audio.codec=pcm
13:41:54.365 video primo fotogramma: hev1.1.6.L150.B0 · … HEVC 8 bit via hevc_vaapi
```

⛔ **`banchi/01-b3-cliente.py` · `--video-codec` declares `--video-codec` with default `hevc,av1`**, and the
server chooses **HEVC**. ⇒ **All the bandwidth numbers of §3.8 and of the first part of this section —
0.204 · 1.179 · 21.36 · 58.668 Mbit/s — are HEVC numbers.**

⛔⛔ **And the product does NOT send HEVC to Firefox Android**: `MEMORY.md`, *«AV1 esce, entra H.264 —
Firefox Android non ha né HEVC né AV1; `avc1.640032` è già verificato»*.

### 13.5.1 `[M]` HOW MUCH IT CHANGES — *same scene, same canvas, same QP 26, 13:47*

| `barra`, 2560×1080, cap off | HEVC | ⭐ **H.264** |
|---|---|---|
| frames/s | 34.67 | ⭐ **41.80** |
| video payload | **21.183** Mbit/s = **105.9 %** | ⭐⭐ **7.920** Mbit/s = **39.6 %** |
| wire | 24.052 = 120.3 % | ⭐ **10.511** = **52.6 %** |
| average bytes per frame | 61 100 | **23 683** |

⛔⛔ **H.264 costs HERE a third of HEVC**, not more. ⚠ It is not codec theory: it is that **`QP 26`
does not mean the same quality in the two**, and on this driver's `hevc_vaapi`, at QP 26 and
`EncSliceLP`, **much more stuff** comes out. ⇒ ⛔ **The degradation ladder (26 → 35 → 44 → 51) is
tuned on a number that means two different things in the two codecs**, and so far it has been tested on the
wrong codec.

⇒ ⭐⭐ **Contradiction §10.1 must be rewritten.** *«It asks for 293 %»* is HEVC. On the codec the
product really sends, the same hard scene asks for **39.6 %** of the floor. ⛔ `[?]` **The real hard
case (film with grain) under H.264 was NOT measured**: it is the first number to take.

### 13.5.2 ⛔ `[R]` AND A DEFECT THAT COMES OUT OF THE SAME LINE: **under H.264 the decoder string is EMPTY**

```
HEVC   → primo fotogramma: hev1.1.6.L150.B0 …   stringa per il decodificatore «hev1.1.6.L150.B0»
H.264  → primo fotogramma: (non letto)      …   stringa per il decodificatore «»
```

⛔ Under H.264 the server **does not compose** the string `avc1.<profilo><vincoli><livello>` (the comment
that describes it is in `codificatore.c` · `salta_liste_scala()`), and writes `(non letto)`. ⚠ **It reads the level
anyway** (`livello 51`, then `52`): what is missing is the **string**. `[?]` If it is the one that goes to the browser, it is the
R31 family — *«it does not give a network error, it makes the configuration be refused»*.

## 13.6 ⛔⛔⛔ 4K — *13:50-13:52*: **41 frames/s, not 60 — and the produced level EXCEEDS the client's**

**The round**: canvas **3840×2160** verified **in the product's log** (`TELA NUOVA DAL PALCO:
1920x1080 → 3840x2160`), scene `barra`, 20 s, cap off, `tc` never touched.

| at 3840×2160 | ⭐ **H.264** (what the browser receives) | HEVC |
|---|---|---|
| **frames/s** | ⛔ **41.25** | 38.75 |
| video payload | **24.055** Mbit/s = **120.3 %** of the floor | ⛔ **74.390** = **372.0 %** |
| wire | 26.711 = 133.6 % | ⛔ **78.018** = **390.1 %** |
| average bytes per frame | 72 895 | 239 968 |
| keyframes / abandons in 20 s | ⭐ **0 / 0** | ⛔ **19 / 20** |
| ⛔ **PRODUCED LEVEL** | ⛔⛔ **5.2** (`level_idc` 52 in the SPS) | 5.0 (`general_level_idc` 150) |

### 13.6.1 ⛔ THE ANSWER TO THE QUESTION: **the 4K·60 the product promises is not there, and the cap is not the line**

⭐ **41.25 fps with the line FREE** (no `tc`, no loss, zero abandons, zero keyframes).
⇒ ⛔ **It is not bandwidth that stops it**: it is the chain capture → conversion → encoding.
The line of the first frame at 4K gave conversion + encoding as the cap of the chain even before
leaving home. *(Those times no longer hold after phase 18: the conversion of that frame is not
proven to be zero copy — the code of the time also had the route from memory with `sws_scale` — and they were
removed.)*
⇒ **`DECISIONI.md` must be corrected: at 3840×2160 the product holds ~41/s, not 60.**

### 13.6.2 ⛔⛔ AND THE RED OF **P9** HAS FALLEN, with a concrete trigger

```
rcp    il client dichiara video.livello=5.1 … §4.3 vieta al server di emettere un flusso PIU' ALTO
figlio §4.3 — LIVELLO PRODOTTO: 5.2 (nell'SPS e' 52) … il confronto fra le due righe lo fa CHI
       LEGGE — il programma NON lo fa
```

⛔⛔ **The server emitted 5.2 where the client admitted 5.1, and nobody said anything.** It is
exactly the defect §5.5 had found by reading the code (`rcp.c` · `livello_legge()` does not capture the
level) and that **P9** predicted: *«a level too low does not give a network error: it makes the
configuration be refused, that is a screen that does not start without a red»*. ⭐ Now it is no longer a reading of the
code: **it happened, at 13:50:48, and the two lines are in the log.**

⚠ **And the estimate of §5.5 was wrong in yet another way**: it said *«at 4K 5.1 is needed, which
grants `[?]` 30.3 fps»*. `[M]` `h264_vaapi` did not choose 5.1: **it chose 5.2**. ⇒ the number
to put in `pagina.html` · `LIVELLO_DICHIARATO()` is not `avc1.640033` (5.1) but `avc1.640034` (5.2) **if one really wants
4K** — ⛔ and it must be verified that Firefox Android accepts 5.2, because otherwise the choice
is **between 4K and that browser**.

## 13.7 ⛔ AUDIO — **skipped, and I declare why**: the bench cannot open Marionette

⭐ The bench `banchi/09-b74-audio-firefox.py` (written today) is **the right shape** and solves the
defect of §3.16: the *before* and the *after* are **two `pagina.html` files**, served by the **same
binary**, and the record is the `/diario` line that **the page sends by itself** to the server every 5 s.
⭐ And the service started well: `pagina: /media/REMOTIX/src/09-src/src/pagina.html ·
md5 d387c166…` for the *before* — that is **the OLD page, and it shows from the `md5`**, not from the name.

⛔ **But Firefox never opens Marionette's port 2829.** Two attempts (13:53 and 13:55), plus a
diagnosis: **80 s of waiting, the port never appears**. ⇒ The arm does not start, and **without the
«before» arm there is no positive control**: a clean *after* alone would prove nothing.

⚠ **And the diagnosis stopped on a bench defect inside the bench**: `b74-ff.log` is created in
`$LAV`, which **belongs to root**, while Firefox runs as `prova` ⇒ ⛔ **Firefox's log is ZERO
bytes**, and when one asks *«why didn't it start»* there is nothing to read. It is the **same defect
as the empty `user.js`** that the bench's comment says it already paid for at 12:47, in another
spot of the same file.

⇒ **Cure 4 (the audio reorder) remains NOT VERIFIED.** ⛔ And *«the bench measures
itself»* of §3.16 remains, because `01-b3-cliente.py` still has its copy of the old rule
(`md5 13e68d19ed44298b7926cded53affdda`, unchanged). ⭐ **But the road is short**: the page sends the
record by itself, so **it is enough for Nic to open the page with his browser** and the server's
log carries the three counters (`vecchi` · `tardivi` · `fuori`). Marionette is not needed for the judgement:
it is needed for automation.

## 13.8 ⭐⭐⭐ §10.2 DECIDED — **the border of the spiral lies between 10 and 5 Mbit/s**, and above it does not bite

⛔ The question of §10.2 was: *«above the floor does the spiral bite or not?»*, with **two positions** in
the field — §5.2 (*«the defect lives below the floor, above the cure is inert»*) against §3.10
(*«abandons and keyframes also on the wide line, 3↔3 at 22-26 Mbit/s»*).

**The round that decides it**: ⛔ **on the REAL DESKTOP**, not on `barra` — ⭐ and with the **codec the browser
really receives, H.264** (`negoziato video.codec=h264`, read from the log). A **single** session at
2560×1080 for all the steps, so the only variable is the squeeze. Threshold and regulator **off**,
that is the product as it is today. Step: 8 s wide → **3 s narrow** → 6 s wide.

| the squeeze | frames sent | ⛔ **KEYFRAMES** | ⛔ **abandons §5.1** |
|---|---|---|---|
| **30 Mbit/s** (150 % of the floor) | 421 | ⭐ **0** | ⭐ **0** |
| **25 Mbit/s** (125 %) | 429 | ⭐ **0** | ⭐ **0** |
| ⭐ **20 Mbit/s** (**the floor**) | 426 | ⭐ **0** | ⭐ **0** |
| **15 Mbit/s** (75 %) | 406 | ⭐ **0** | ⭐ **0** |
| **10 Mbit/s** (50 %) | 426 | ⭐ **0** | ⭐ **0** |
| ⛔ **5 Mbit/s** (25 %) | 424 | ⛔ **3** | ⛔ **3** |

### ⭐ THE VERDICT, flat

⛔⛔ **On real content the spiral does NOT exist down to 10 Mbit/s inclusive**, that is down to **half the
floor**. The first sign arrives at **5 Mbit/s**, and it is **3 keyframes out of 424 frames = 0.7 %**.
⇒ **§5.2 was right and §3.10 was measuring something else**: its abandons at 22-26 Mbit/s were on
**`barra`**, the halftone gradient — a **synthetic** scene that at 2560×1080 costs **21 Mbit/s by
itself** (105.9 % of the floor). ⛔ **It is nobody's desktop**: it is a test case that lives
*above* the floor even at rest, and under that load any squeeze produces a queue.

⇒ ⭐⭐ **The queue threshold and the rate regulator are ROBUSTNESS MEASURES, not corrections of a
defect the user sees.** On his desktop, at 20 Mbit/s, **they have nothing to do** — and it is what
P2 and P7 predicted. ⚠ They are needed when the line drops **below half**, or when the
content is a hard case (full-screen video), and there they work well: §13.3.

⚠ **The defect of my script, declared**: the per-second table I had printed gave
`fot [0,0,0]` in all six rounds — an error of mine in grouping by second, **not a measurement**.
⛔ The numbers above **do not come from that table**: they come from the **direct count on the saved
logs** (`grep -c SPEDITO`, `grep -c 'SPEDITO: CHIAVE'`, `grep -c ABBANDONATO`), which is the
quantity the product writes. ⚠ Had I reported the table, I would have said *«zero frames»*
where there were **424**.

## 13.9 ⭐⭐⭐ THE VERDICT OF THE EVENING — the nine predictions, one per line

| # | the prediction | outcome | where |
|---|---|---|---|
| **P1** | the crash reproduces; with the cure it holds | ⭐⭐⭐ **CONFIRMED, and beyond**: the sick one dies at frame **27** (516 782 bytes), the cured one holds **1 463** frames up to **537 063** bytes with 5 % loss. ⭐ **The stack from the core closes the `[?]` of §4.8** | 13.1 |
| **P2** | the threshold is **inert** at 20 Mbit/s | ⭐ **CONFIRMED**, and not only at 20: on the real desktop **nothing to do down to 10 Mbit/s** | 13.2.2 · 13.8 |
| **P3** | on the step: keyframes ≤ 2/s, abandons ≤ 2/s, fps ≥ 25 | ⛔ **REFUTED on the two numbers that counted**: keyframes **4-5/s**, abandons **5-9/s**. ⭐ Confirmed on inertia and return. ⛔ **And the remedy written in P3 was in the wrong direction** | 13.2.2 · 13.2.3 |
| **P4** | the cap: real desktop **does not go down**, halftone **below the floor** | ⭐⭐⭐ **CONFIRMED — the two reds that would throw the cure away did NOT fall**: 0.208 → **0.249** (+19.7 %), halftone 21.18 → **8.29**. ⚠ It squeezes **more** than predicted (out of the range at the bottom) | 13.4 |
| **P5** | the quality climb-back | ⛔ **NOT TESTED** — see 13.10 | 13.10 |
| **P6** | the audio reorder | ⛔ **NOT TESTED**: Marionette does not open the port | 13.7 |
| **P7** | the regulator: **zero descents** with a normal desktop; descents on the step, RISALE within 1 s | ⭐⭐⭐ **FULLY CONFIRMED**: `arretrato` **READ 36-42 times/s** on the wide line with **maximum 0** and **zero descents**; **57** descents concentrated in the 3 s; RISALE **355 ms** after the return. ⛔ And the red *«it is the browser's window»* **did not fall**: `cwnd_left` = 0 | 13.3 |
| **P8** | with a still scene the rate does not drop | ⚠ **NOT measured in pairs** (half still / half moving). ⭐ But half of the check is there: the lines `arretrato LETTO N volte` exist and distinguish *empty* from *forbidden* | 13.3.2 |
| **P9** | the produced level against the client's, and nobody compares them | ⛔⛔ **FALLEN, with the trigger**: at 4K H.264 the server emits **5.2** while the client declares **5.1**, and **the program does not notice** | 13.6.2 |

### ⭐⭐ AND THE THREE NEW THINGS, which no prediction had foreseen

1. ⛔⛔⛔ **HEVC was being measured.** The test client negotiates `hevc`, the product sends H.264 to
   Firefox. Same scene: **21.18** Mbit/s in HEVC against **7.92** in H.264 — ⇒ **§10.1 must be
   rewritten and the bill redone** — 13.5;
2. ⭐⭐⭐ **The threshold is not a filter: it is the working point of the queue.** At 100 ms the queue settles
   at 101-138; at 200 ms at 204-236. ⇒ raising it **buys image and pays delay**, and does not change the
   number of abandons — 13.2.3;
3. ⭐⭐⭐ **The regulator makes the threshold useless on the step**: it keeps `arretrato` at 2, the queue never
   reaches the 100 ms, and `video_sgombra()` **does not fire even once** — 13.3.1.

## 13.10 ⛔ `--qualita-risale` — **I did not make it fire, and I declare why**

⭐ **It is not a failed attempt: it is an outcome, and it is read in the code before on the hardware.** The line
the product writes by itself at every opening of the encoder:

```
la risalita della qualita' e' SPENTA (invariante I6) … da spenta questi numeri
(120 fotogrammi, 2097152 byte, scalino 9, punto di lavoro QP 26 costante, tetto d'attesa 3840)
non hanno nessun effetto
```

⛔ **`2 097 152` bytes = 2 MiB is the threshold that makes quality GO DOWN.** For the climb-back to have
something to climb back, quality must first have gone down, that is a frame **above 2 MiB** is needed.
`[M]` tonight, the **largest frame ever seen in the whole day**: **537 063 bytes** — a
**quarter** of the threshold, and on a **film with grain at full screen**, which is the hardest case
this phase has. At 4K HEVC the average is **239 968** bytes, the peak stays far away.
⇒ ⛔ **On the user's canvas it never happens**, and it is the same thing §5.3 had written.

⚠ **The road to make it fire exists and it is the one declared in the mandate** — huge canvas + software
fallback (`h264_vaapi` stops at 4096 px per side) — ⛔ **but it is a round that does not measure the product**:
it would measure the software encoder on a canvas no user has. ⇒ **I did not do it**, and
cure 3 remains **not verified on the hardware**. ⭐ What is verified is that **it is off and says so**, and
that when off **it touches nothing**: the numbers of the paired comparison of §3-bis already showed it.

## 13.11 ⭐ HOW THE MACHINE WAS LEFT — *verified at 14:01 UTC, not declared from memory*

| | |
|---|---|
| `tc` on **`lo`** | ⭐ `qdisc noqueue 0: root` — **no discipline** |
| `tc` on **`enp7s0`** | ⭐ `qdisc mq 0: root` — **never touched**, as per the rule |
| the `tc` **guardian** | ⭐ none: `.b68-guardiano.pid` is not there |
| **scenes, clients, browsers** | ⭐ **none** — neither `04-b30-scena`, nor `01-b3-cliente`, nor `firefox` |
| **`core_pattern`** | `/media/REMOTIX/tmp/09c/core.%e.%p.%t` — ⚠ **it was already so before I started** (`core_pattern.prima` says the same), and it is what §4.7 point 1 asked: **absolute**. ⛔ It is not the factory value (`core`): **I leave it**, because it is the armed trap, ⚠ and I declare it because it is a state of the machine, not of the project |

**The three ports that stay on, and why:**

| port | tree | why it stays |
|---|---|---|
| **7900** | `09-src` | ⭐ this morning's **BEFORE** — the term of comparison of §3-bis. ⛔ Switching it off would make all the paired measurements already written unrepeatable |
| **7910** | `09b-src` | the three morning cures, the other half of the same comparison |
| **7920** | `09c-src` (`remotix md5 162d2d105cbe930e7921a7041053f5e7`) | ⭐ **tonight's cured one**, rebuilt from `f90eb21`, **with no switch on** and with the **glibc trap off** — that is the product as it is |

⭐ **And the corpus delicti is kept**: `/media/REMOTIX/tmp/09c/core.remotix.110832.1787493803`,
**48 525 312 bytes** — the core of the sick binary. ⛔ **It is not deleted**: it is the *seen* proof of the
crash of 23 Aug. ⚠ **And it is not the one of 13.1.1**: see 13.1.5 below, which tells why.

---

# §14 · ⛔⛔⛔ THE YARDSTICK CHANGED — *23 Aug 2026, late evening*

> ⛔⛔ **I CHANGED THE YARDSTICK, AND I SAY IT BEFORE THE NUMBERS.**
> Until 14:22 today every bench round of this phase measured **HEVC**; from here down
> it measures **H.264**, which is the codec the user's browser really receives. ⇒ ⛔ **The bandwidth
> numbers of §3.8, §3.15, §13.4 and §13.5 are not compared with those of §14.** They are two scales.
> ⭐ The old yardstick is redone when needed: `--video-codec hevc`.

## 14.1 ⭐⭐ LA CURA DEL CLIENTE DI PROVA — e **come lo decide il browser vero**, verificato

### La riga cambiata

`banchi/01-b3-cliente.py` — il predefinito di `--video-codec` era **`hevc,av1`**, adesso è
**`h264`**. ⛔ **La causa non è una svista di stasera: è una riga rimasta indietro di tre giorni.**
Il 20 agosto AV1 è uscito dal prodotto (`DECISIONI.md` §1.13-ter) e il cliente di prova ha
continuato a dichiarare `hevc,av1` — ⇒ il server sceglieva **HEVC** in ogni giro, per tre giorni.

### ⛔ E LO DECIDE IL BROWSER? — verificato, non assunto

⭐ `pagina.html` **non** chiede il codec alle API, e lo dichiara in testa al file: `[M]` 12 agosto,
su tutte e sette le stringhe HEVC `mediaCapabilities.decodingInfo()` e `canPlayType()` dicono di
**sì** e il pixel non arriva. ⇒ La pagina **dipinge una sonda vera e rilegge i pixel**, e nel `CIAO`
ci finisce solo quel che ha dipinto:

```
pagina.html:818   const PREFERENZA = ["hevc", "h264"];        ⛔ AV1 non c'è più
pagina.html:4672  const codec_buoni = PREFERENZA.filter((n) => …sondaggio…arriva);
pagina.html:4725  ["video.codec", codec_buoni.join(",")]
```

⇒ **Su Firefox HEVC non dipinge ⇒ la pagina manda `video.codec=h264` e basta.** Il predefinito
nuovo del cliente è **esattamente quello**, non un'approssimazione.

### `[M]` LA PROVA CHE IL METRO È CAMBIATO — *14:22:06-07 UTC*, righe testuali dal registro

```
14:22:06.637 rcp     negoziato video.codec=h264 video.profondita=8 audio.codec=pcm
14:22:07.782 video   primo fotogramma: (non letto) · 25450 byte · … livello 51, 2560x1080 ·
                     conversione … µs, … codifica … µs · H.264 8 bit via h264_vaapi
```

*(I tempi di conversione e codifica della riga sono tolti dopo la fase 18: la conversione non si dimostra
a copia zero.)* *→ conversione (in CPU) e codifica del primo fotogramma a 4K senza scheda: `fasi/18-senza-ffmpeg.md` §5.4.*
⚠ Il giro delle 14:03, con lo stesso binario e il cliente vecchio, diceva
`hev1.1.6.L150.B0 … HEVC 8 bit via hevc_vaapi`. **Stesso server, stesso minuto, due codec.**

### 14.1.1 ⛔ LA STRINGA VUOTA — **è un difetto del PRODOTTO, non del banco**, e vale meno di quanto sembrava

`[R]` di §13.5.2 verificato riga per riga sull'albero congelato `09c-src`:

```
codificatore.c:953   snprintf(c->stringa_codec, …, "hev1.%s%u.%X.%c%u%s", …)   ← HEVC
codificatore.c:1152  snprintf(c->stringa_codec, …, "av01.%u.%02u%c.%02d", …)   ← AV1 (codice morto)
                     ⛔ e per H.264 NON C'E' NESSUNA RIGA: `avc1.` non si compone da nessuna parte
codificatore.c:4065  c->conf.stringa_codec[0] ? … : "(non letto)"
```

⇒ ⛔ **Difetto del prodotto**: `stringa_codec` non viene mai composta sotto H.264, e il registro
scrive `(non letto)` e `«»`.

⭐⭐ **Ma NON è la famiglia di R31, e questo cambia la sua gravità.** L'unico uso di
`stringa_codec` fuori dal codificatore è `figlio.c` ⚠ *(il codice citato non c'e' piu': da rileggere)* e `:4780`, e sono **due righe di
registro**: la stringa **non parte mai verso il browser**. Quella che il browser usa davvero se la
compone la pagina da sé, dal livello che **lei** dichiara:

```
pagina.html:1182   return ["avc1.6400" + esa(idc), "avc1.64001f"];   /* idc da LIVELLO_DICHIARATO */
```

⇒ ⭐ **Il difetto è una CECITÀ DELLA DIAGNOSI, non uno schermo nero**: sotto H.264 il registro non
sa dire quale stringa servirebbe, e chi legge non può confrontarla con quella che la pagina
manda. ⛔ **E la cecità morde proprio dove serve**: a 4K il server produce il livello **5.2**
(§13.6.2) mentre la pagina configura `avc1.640033`, cioè **5.1** — e la riga che avrebbe reso
visibile lo scarto è quella vuota.

## 14.2 ⭐⭐⭐ LE CINQUE SCENE A 2560×1080 IN H.264 — *14:23:08 → 14:26:26 UTC*

**Il giro**: porta **7920**, binario `md5 162d2d10…` (`f90eb21`, nessun interruttore, trappola
glibc spenta), utente **`prova2`**, tela **2560×1080**, **una sola sessione** per tutti e cinque i
punti — così l'unica variabile è la scena. Tetto **spento**, `tc` **mai toccato** (`lo` verificata
`noqueue` prima e dopo, `enp7s0` mai sfiorata). 30 s per punto.

| scena | ora | fot/s | ⭐ **carico video H.264** | % di 20 | filo `lo` | byte/fotogramma | chiavi | abbandoni |
|---|---|---|---|---|---|---|---|---|
| **ferma** (nessuna scena) | 14:23:08 | 0,00 | **0,000** Mbit/s | 0 % | 2,427 | — | 0 | 0 |
| ⭐ **desktop VERO** (`scena-utente.webm` a schermo intero) | 14:23:52 | 23,10 | **0,356** Mbit/s | **1,8 %** | 2,842 | 1 924 | 0 | 0 |
| **tinta piatta** (`pieno`) | 14:24:31 | 41,03 | **1,190** Mbit/s | 5,9 % | 3,717 | 3 624 | 0 | 0 |
| **gradiente retinato** (`barra`) | 14:25:10 | 40,77 | **7,728** Mbit/s | 38,6 % | 10,45 | 23 695 | 0 | 0 |
| ⛔ **film con la GRANA** (il caso duro) | 14:25:55 | 23,30 | ⛔ **44,574** Mbit/s | ⛔ **222,9 %** | 48,42 | 239 129 | 0 | 0 |

### ⛔⭐ LA RISPOSTA ALLA DOMANDA CHE DECIDE

> **Il caso duro in H.264 supera i 20 Mbit/s?** ⇒ ⛔ **SÌ. 44,574 Mbit/s, cioè 2,2 volte il
> pavimento.**

### `[M]` I DUE METRI AFFIANCATI — e la distanza **non** è un fattore costante

| a 2560×1080, tetto spento | HEVC (§3.8, mattina) | ⭐ **H.264** (14:2x) | rapporto |
|---|---|---|---|
| ferma | 0 | 0 | — |
| desktop vero | 0,204 | ⚠ **0,356** | ⛔ **1,7× in SU** |
| tinta piatta | 1,179 | 1,190 | 1,01× |
| gradiente retinato | 21,36 | ⭐ **7,728** | **0,36×** |
| film con la grana | 58,668 | **44,574** | **0,76×** |

⛔⛔ **E questa riga è il fatto nuovo della tabella**: H.264 **non** costa «un terzo di HEVC», come
§13.5.1 lasciava credere misurando una scena sola. Costa **il 36 %** sul gradiente retinato, il
**76 %** sul film con la grana e ⛔ **il 170 %** — cioè **di più** — sul desktop vero.
⇒ ⭐ **Il rapporto fra i due codec dipende dal CONTENUTO**, ed è la stessa lezione di §3.8 («quanti
pixel cambiano non predice niente») applicata al codec. ⚠ Un fattore di conversione da HEVC a
H.264 **non esiste**: i numeri vecchi non si convertono, si **rifanno**.

### ⭐ Il controllo positivo, e sta dentro la tabella

I cinque punti coprono **tre ordini di grandezza** (0 → 0,356 → 1,19 → 7,73 → 44,57): se il banco
fosse cieco darebbero lo stesso numero. ⭐ E `barra` ritrovato a **7,728** contro i **7,920** di
§13.5.1, preso trentacinque minuti prima con un'altra sessione: **2,4 % di scarto**, cioè la misura
si ripete.
⚠ **La riga `ferma` dice un'altra cosa che vale la pena leggere**: **zero** video e **2,427
Mbit/s sul filo**. ⇒ A desktop fermo il **100 %** di quel che passa è QUIC + **l'audio PCM**, che da
solo chiede 1,536 Mbit/s. `[?]` **A linea stretta è l'audio a mangiare il video, non il contrario** —
vedi 14.4.1, dove a 3 Mbit/s il video scende a 5 fot/s e il filo resta a 2,4.

## 14.3 ⭐⭐⭐ §10.1 RIFATTA COL NUMERO GIUSTO — la contraddizione **non cade, si dimezza**

§10.1 metteva a confronto due frasi: lo studio diceva *«non serve nessun tetto»* sul contenuto vero,
la misura diceva *«293 % del pavimento»* sul caso duro. ⛔ Erano tutt'e due **numeri HEVC**.

| | HEVC (quel che diceva §10.1) | ⭐ **H.264** (quel che l'utente riceve) |
|---|---|---|
| il **contenuto vero** dell'utente | 0,204 Mbit/s = **1,0 %** | **0,356** Mbit/s = **1,8 %** |
| il **caso duro** (film con la grana) | 58,668 = **293 %** | ⛔ **44,574** = **223 %** |
| la distanza fra i due | **288×** | **125×** |

### ⭐ LA CONCLUSIONE, col numero e non con l'opinione

1. ⭐ **La prima frase regge, e regge meglio di prima**: sul desktop vero il prodotto chiede
   **l'1,8 % del pavimento**. Un tetto a 20 Mbit/s lì **non ha niente da fare**, e §13.4 l'ha già
   misurato (0,208 → 0,249, e la cura non è caduta);
2. ⛔ **La seconda frase regge anche lei, e il cambio di codec NON la salva**: il caso duro chiede
   **223 %** invece di 293 %. ⇒ ⛔ **Passare a H.264 toglie 70 punti percentuali e lascia il
   problema in piedi**: 44,6 contro 20 è ancora **più del doppio**;
3. ⇒ ⭐⭐ **LA CONTRADDIZIONE NON ERA UNA CONTRADDIZIONE, ed è deciso**: le due frasi parlano di due
   contenuti diversi, e tutt'e due sono vere **sullo stesso codec**. **Il tetto serve, e serve solo
   per il caso duro** — cioè è esattamente quel che §5.5 aveva progettato: un parapetto che sul
   desktop vero non si accorge di esistere.
   ⛔ **E chi volesse buttare il tetto adesso deve rispondere a questa riga**: *con quale numero il
   film a schermo intero sta dentro i 20 Mbit/s senza di lui?*

## 14.4 ⛔⭐⭐ LA SOGLIA SULLA CODA, tarata nel verso giusto — *14:27 → 14:35 UTC*

### 14.4.1 ⛔⛔ IL BANCO CHIESTO NON HA UN CONTROLLO POSITIVO, e lo dico prima dei numeri

Il mandato chiedeva lo spazzamento **sul desktop vero**, e ha ragione: `barra` è sintetico.
⛔ **Ma sul desktop vero non c'è niente da tarare, e l'ho misurato invece di dedurlo.**

`[M]` **14:27:48**, gradino sul desktop vero in H.264, soglia **spenta**, stretta a **3 Mbit/s** —
cioè **un terzo** di quel che §13.8 aveva già provato a 10:

| s | 5-7 (larga) | **8** | **9** | **10** | **11** | 13-25 (larga) |
|---|---|---|---|---|---|---|
| fotogrammi | 29 | 21 | 13 | **5** | 5 | 27-29 |
| ⛔ **chiavi** | 0 | **0** | **0** | **0** | **0** | 0 |
| ⛔ **abbandoni** | 0 | **0** | **0** | **0** | **0** | 0 |

⇒ ⭐⭐ **A 3 Mbit/s — il 15 % del pavimento — sul desktop vero il ritmo crolla da 29 a 5 fot/s e
la spirale NON PARTE LO STESSO: zero chiavi, zero abbandoni.** §13.8 si fermava a 5 Mbit/s e ne
trovava 3; qui, più in basso ancora, ce ne sono **zero**.
⇒ ⛔ **Uno spazzamento della soglia su questa scena misurerebbe zero contro zero contro zero**, cioè
niente. Il banco non ha lo stimolo, e un banco senza stimolo dà *«la cura funziona»* per ogni
valore. **Non l'ho fatto lì.**

⭐ **E c'è un secondo motivo, e viene dal metro nuovo**: l'obiezione di §13.8 contro `barra`
(*«a 2560×1080 costa 21 Mbit/s da sola, non è il desktop di nessuno»*) era un'obiezione **HEVC**.
In H.264 `barra` costa **7,73 Mbit/s** (14.2), cioè il 39 % del pavimento. ⚠ Ma il caso che
**chiede** la cura è un altro, ed è quello vero: il **film con la grana**, 44,6 Mbit/s.

### 14.4.2 `[M]` LO SPAZZAMENTO, sul CASO DURO — film con la grana, 2560×1080, H.264

**Il giro**, identico sei volte: 8 s larga → **3 s a 10 Mbit/s** → 17 s larga, `tc` solo su `lo`
e solo sulla 7920, guardiano armato, `enp7s0` mai toccata (verificato dopo ogni braccio).
Server riavviato a ogni braccio, `md5 162d2d10…`, trappola glibc spenta. Le righe qui sotto sono
**i 3 secondi di stretta**, e i millisecondi sono quelli che il prodotto scrive da sé nella riga
*«la coda del video passa SOPRA la soglia (… byte = N ms …)»*.

| braccio | ora | fot/s nei 3 s | ⛔ chiavi | ⛔ abbandoni | kbyte | attrav. | ⚠ **ms di coda pagati** | `arretrato` max |
|---|---|---|---|---|---|---|---|---|
| **spenta** | 14:29 | 6,0 | **8** | **8** | 6 111 | — | — | 0-1 per costruzione |
| **100 ms** | 14:30 | 6,7 | 8 | 10 | 6 507 | 8 | **136 – 397** | 3 |
| **200 ms** | 14:31 | 7,7 | 8 | 14 | 7 216 | 8 | **222 – 942** | 6 |
| **400 ms** | 14:32 | 5,7 | 6 | 8 | 5 930 | 7 | **414 – 643** | 8 |
| **800 ms** | 14:33 | 7,3 | **5** | 14 | 6 738 | 6 | ⛔ **856 – 1 321** | 7 |
| ⭐ **200 + `--ritmo-adattivo`** | 14:34 | 5,3 | 6 | ⭐ **6** | 5 521 | 7 | ⭐ **209 – 323** | ⭐ **2** |

### ⭐ LA COPPIA CHE L'UTENTE DEVE GIUDICARE, e la risposta secca

> **A quale valore la soglia mantiene la promessa di P3, e a che prezzo in ms?**
> ⇒ ⛔ **NESSUNO. Da sola non ci arriva a nessun valore.** P3 chiedeva *chiavi ≤ 2/s*,
> *abbandoni ≤ 2/s* e *fot ≥ 25/s*: ⭐ le chiavi scendono nella promessa a **400 ms** (2,0/s) e a
> **800** (1,7/s), ⛔ gli **abbandoni non ci arrivano a nessun valore** (2,7 – 4,7/s), e ⛔ i
> **fotogrammi non ci si avvicinano nemmeno** (5,3 – 7,7/s contro 25).
> ⭐⭐ **L'unico braccio che porta gli abbandoni dentro la promessa è la COPPIA**
> `--sgombra-soglia-ms 200 --ritmo-adattivo`: **6 abbandoni in 3 s = 2,0/s**, e li paga con
> **209-323 ms** di coda, cioè **~264-378 ms dal gesto al pixel** sommando i 55 ms dell'anello di
> fase 8.

### ⛔⛔ E TRE COSE CHE SMENTISCONO QUEL CHE §13.2.4 AVEVA CONCLUSO

1. ⛔ **«Il miglioramento è monòtono» NON regge sul caso duro.** Le chiavi calano piano
   (8 · 8 · 8 · 6 · 5) ma gli **abbandoni ballano** (8 · 10 · 14 · 8 · 14) e i fotogrammi pure
   (6,0 · 6,7 · 7,7 · 5,7 · 7,3). ⚠ Un solo giro per braccio: **una differenza di una o due chiavi
   è dentro il rumore, e non la riporto come un effetto.** Quel che è **fuori** dal rumore è una
   cosa sola, ed è il prezzo;
2. ⛔⛔ **IL PREZZO CRESCE PIÙ IN FRETTA DI QUEL CHE COMPRA, e a 800 ms è fuori scala**:
   397 → 942 → 643 → **1 321 ms**. ⭐ Il punto di lavoro di §13.2.4 è confermato una seconda volta e
   su un'altra scena (la coda si assesta **appena sopra** la soglia, qualunque numero si scelga) —
   ⛔ ma la conseguenza è che **alzare la soglia compra 3 chiavi e vende un secondo e tre decimi di
   ritardo.** ⇒ **Il verso «alzala» di §13.2.3 è giusto solo fino a ~200-400 ms**: sopra, il
   commercio è quello che `SPECIFICHE.md` §3.2 vieta in una riga;
3. ⭐⭐⭐ **E IL REGOLATORE È LA LEVA, NON LA SOGLIA.** `arretrato` massimo: **3 · 6 · 8 · 7** con la
   sola soglia, ⭐ **2** con la coppia — cioè `WT_RITMO_POSTI = 2` **tiene**, e la coda smette di
   approfondirsi. ⇒ Alla stessa soglia di 200 ms, accendere il regolatore **dimezza gli abbandoni
   (14 → 6)** e **taglia il ritardo di massimo da 942 a 323 ms**. ⛔ **La soglia da sola non è la
   leva giusta; la coppia sì**, ed è quel che il mandato sospettava.

⚠ **Il rosso di §2 del mandato resta in piedi e lo dichiaro**: se il ritardo dell'anello superasse
55 ms + la soglia, la stima dello svuotamento sottostima. `[M]` qui la coda misurata arriva a
**1 321 ms** contro una soglia di 800: ⇒ ⛔ **a 800 ms la stima È già fuori dal suo campo di
validità**, ed è una ragione in più per non salire lì.

## 14.5 ⭐⭐⭐ P8 — IL RITMO A SCENA FERMA, A COPPIE: **VERDE** — *14:40:00 → 14:41:00 UTC*

**Il giro**: `banchi/09-b75-p8.py` (nuovo), porta 7920 con **tutt'e due gli interruttori**
(`--sgombra-soglia-ms 100 --ritmo-adattivo`, letti dalla riga d'avvio del prodotto, non dedotti dal
comando), tela 2560×1080, H.264, linea **larga**, **tre coppie** ferma/mossa da 8 s **alternate
nello stesso giro**. Il verbale è la riga che `ritmo_ciclo()` scrive **col battito e non coi
fotogrammi**, una al secondo.

| | secondi | ⭐ **`arretrato` LETTO** | secondi con **ZERO** letture | massimo | ⛔ **discese** |
|---|---|---|---|---|---|
| ⛔ **metà FERMA** | 16 | **0 in tutto** | ⭐ **16 su 16** | 0 | ⭐ **0** |
| ⭐ **metà MOSSA** | 27 | **1 072** = **39,7 al secondo** | ⭐ **0 su 27** | 0 | ⭐ **0** |

⇒ ⭐⭐⭐ **VERDE, e sui due punti insieme**: nella metà ferma il ramo **non è stato percorso**
(«LETTO 0 volte», 16 righe su 16) e il ritmo **non è sceso**; nella metà mossa l'anello è stato
percorso **1 072 volte** e il ritmo **non è sceso lo stesso**.
⛔ **E questo è quel che «il contatore è zero» non poteva dire**: le due metà danno lo stesso zero
di discese, e le righe `LETTO` dicono che **una l'ha guadagnato e l'altra no**. Vuoto e proibito
sono distinti, che è tutto il punto di P8.

⭐ **E `massimo 0` nella metà mossa è il secondo fatto**: su linea larga `arretrato` non arriva
neanche a 1. ⇒ Il regolatore è **un parapetto che non tocca niente**, com'era previsto (P7, S.5).

### ⛔ DUE DIFETTI DEL BANCO TROVATI STRADA FACENDO — e tutt'e due davano «un numero plausibile»

1. ⛔ **La tappa «mossa» era segnata DOPO l'accensione.** `09-b68-scena.sh` lancia la scena e poi
   **dorme 2 s** per verificare che sia viva: quei 2,3 secondi, in cui la scena **dipinge già**,
   finivano nella metà **ferma**. `[M]` 14:37 — la metà ferma usciva con **26 righe invece di 18** e
   **147 letture**, e il banco diceva **GIALLO su un giro sano**;
2. ⛔ **Il primo secondo dopo la morte della scena porta ancora 22-40 letture.** Non è il prodotto
   che non si ferma: **uccidere il processo della scena non ferma Mutter**, e i fotogrammi già
   composti continuano ad arrivare per circa un secondo. ⇒ Si butta **2,5 s di guardia** dopo ogni
   cambio, **e si dichiara**: contarli da una parte o dall'altra sarebbe attribuire al prodotto un
   transitorio del compositore. ⚠ **E la guardia non può nascondere il rosso che conta**: una
   discesa a scena ferma cadrebbe nei secondi **centrali**, non sul bordo.

## 14.6 ⭐⭐ IL 4K IN H.264 — *14:45:42 → 14:48:15 UTC*: **il numero che mancava, e il tetto SI MUOVE**

**Il giro**: stessa 7920, stesso binario, **nessun interruttore**, tela **3840×2160** verificata nel
registro del prodotto (`SESSIONE: stato=1 tela=3840x2160`), `tc` mai toccato, 30 s per punto,
una sola sessione.

| a **3840×2160**, H.264, tetto spento | fot/s | ⭐ **carico video** | % di 20 | filo | byte/fotogramma | chiavi | abb. |
|---|---|---|---|---|---|---|---|
| ⭐ **desktop VERO** | 23,10 | **0,852** Mbit/s | ⭐ **4,3 %** | 3,351 | 4 607 | 0 | 0 |
| **tinta piatta** (`pieno`) | ⚠ **33,37** | 2,716 | 13,6 % | 5,259 | 10 174 | 0 | 0 |
| **gradiente retinato** (`barra`) | **40,40** | 23,564 | **117,8 %** | 26,641 | 72 908 | 0 | 0 |
| ⛔ **film con la GRANA** | 23,27 | ⛔ **74,699** | ⛔ **373,5 %** | 79,279 | 401 320 | ⛔ **2** | ⛔ **2** |

### ⭐ 1. IL TETTO DEI 41 FOT/S **SI MUOVE CON LA SCENA** — e §13.6 non poteva vederlo

§13.6 aveva misurato **41,25 fot/s** su `barra` e ne aveva concluso *«a 3840×2160 il prodotto regge
~41/s»*. ⭐ Con quattro scene invece di una si vede che **non è un tetto, è un punto**: `barra`
**40,40**, ⚠ `pieno` **33,37** — cioè **7 fotogrammi in meno su una scena che costa NOVE VOLTE
MENO banda** (2,7 contro 23,6 Mbit/s).
⇒ ⛔ **Non è la banda a decidere il ritmo a 4K**, e non è neanche il costo della codifica: è quel
che **il compositore consegna**, ed è la stessa lezione di §3.1. ⚠ I due punti `video` (23,1 e
23,27) **non dicono niente sul tetto**: è il filmato stesso che gira a ~23/s.
⇒ **`DECISIONI.md` va corretto così**: a 3840×2160 il prodotto regge **33-41 fot/s a seconda della
scena**, non 60 e nemmeno «41».

### ⭐ 2. QUANTO COSTA IL 4K, e cresce **quasi coi pixel** (ma non sul caso duro)

I pixel a 4K sono **3,0×** quelli di 2560×1080. `[M]` la banda:

| scena | 2560×1080 | 3840×2160 | rapporto |
|---|---|---|---|
| desktop vero | 0,356 | 0,852 | **2,4×** |
| tinta piatta | 1,190 | 2,716 | **2,3×** |
| gradiente retinato | 7,728 | 23,564 | **3,05×** |
| ⛔ film con la grana | 44,574 | 74,699 | ⚠ **1,68×** |

⭐ **La riga che conta per l'utente**: a **4K** il suo desktop vero costa **0,852 Mbit/s, il 4,3 %
del pavimento**. ⇒ ⛔ **Il 4K non è un problema di banda**: è un problema di **fotogrammi**.
⚠ E il caso duro cresce **meno** degli altri (1,68× invece di 3×) perché a 2560 era **già** al
limite di quel che la catena riesce a produrre.

### ⛔ 3. IL PRIMO SEGNO DI CEDIMENTO SU LINEA LIBERA

Il film con la grana a 4K è l'**unico** punto di tutta la sera che ha prodotto **chiavi e abbandoni
con `tc` mai toccato**: 2 chiavi, 2 abbandoni, 1 chiave trattenuta da §5.2 in 30 s.
⇒ ⭐ A **79,3 Mbit/s sul filo** la coda comincia a non svuotarsi **anche senza nessuna
strozzatura**. ⚠ È il punto in cui «linea larga» smette di essere larga.

### ⛔⛔ 4. E P9 SI RIPRODUCE COL METRO NUOVO — *14:42:50-51*, due righe a un secondo di distanza

```
14:42:50.068 rcp     il client dichiara video.livello=5.1 … §4.3 vieta al server di emettere
                     un flusso PIU' ALTO di questo
14:42:51.328 figlio  §4.3 — LIVELLO PRODOTTO: 5.2 (nell'SPS e' 52) · stringa per il
                     decodificatore «»
```

⛔ **Il server emette 5.2 dove il client ammette 5.1, e il programma non se ne accorge** — §13.6.2
non era un caso del giro di allora: si ripete **ogni volta** che la tela è 4K.
⚠ Il tetto «conversione + codifica» del primo fotogramma stava sopra i 40,40 di `barra`. *(I tempi sono
tolti dopo la fase 18: la conversione non si dimostra a copia zero.)* *→ in software: `fasi/18-senza-ffmpeg.md` §5.4.*

## 14.7 ⛔ L'AUDIO — **ancora NON verificata**, ma la causa di due sere è trovata e curata

⭐ **§13.7 accusava il browser, e sbagliava imputato.** La riga che chiude il caso, `[M]` 23 agosto
**14:49**, col registro creato **prima**, con l'uid giusto e i permessi giusti:

```
⛔ Marionette non ha aperto la 2829 in 40 s.
   firefox vivo? ⛔ NESSUN PROCESSO
   il suo registro (/tmp/b74-ff.log): ⛔ VUOTO
```

⇒ ⛔⛔ **Non era Marionette a non aprire la porta: era Firefox a non partire affatto.**

### ⛔ 14.7.1 LA CAUSA, e sono TRE difetti in fila — due miei, uno del sistema

1. ⛔⛔ **Il lanciatore era una riga di comando invece di un file.**
   `root("bash -c \"setsid nohup setpriv … firefox … &\"")`: `bash -c` mette il lavoro in
   sottofondo ed **esce nello stesso istante**, `sudo` esce dietro di lui e `ssh` chiude la
   sessione — il processo **muore nella corsa** prima che `setsid` l'abbia staccato.
   ⭐ **Curato**: `banchi/09-b74-ff.sh`, la stessa forma di `09-b72-video.sh` che funziona dal
   mattino — un **FILE**, e il padre resta vivo mentre il figlio si stacca. ⚠ È la terza volta
   oggi che la cura è *«un copione lungo si spedisce come file»*;
2. ⛔ **`fs.protected_regular = 2`** (verificato con `sysctl`): in una cartella **sticky** come
   `/tmp`, **nemmeno root** può aprire in scrittura un file **world-writable** che appartiene a un
   altro utente — ed era esattamente quel che il tentativo precedente aveva lasciato lì.
   `[M]` `cannot create /tmp/b74-ff.log: Permission denied` **da root**.
   ⭐ **Curato**: si **cancella** e si ricrea (il permesso è della cartella, non del file);
3. ⛔ **E adesso Firefox parte, resta vivo — e la prova NON si chiude lo stesso.** `[M]` 14:52:
   `firefox-esr 140.14.0esr`, tre processi vivi con `--profile /tmp/b74-ff --marionette`,
   `MOZ_MARIONETTE=1` **letto da `/proc/PID/environ`**, `marionette.port = 2829` in un `user.js`
   di **487 byte** — e ⛔ **`ss -tlnp` non mostra NESSUN socket in ascolto del processo Firefox**,
   né sulla 2829 né sulla 2828.

### ⛔⛔ 14.7.2 E C'È UN SECONDO MURO DIETRO IL PRIMO, che il registro del prodotto dimostra

Nel registro della 7920 **non c'è nessuna richiesta della pagina da parte del browser**: dopo
`ascolto TCP su 0.0.0.0:7920` l'unica stretta di mano è quella del cliente di prova.
⇒ ⛔ **Firefox non ha mai chiesto la pagina.** Il certificato è **autofirmato**, e senza
`acceptInsecureCerts` — che è una funzione **di Marionette** — il browser si ferma
all'avviso e non emette la richiesta.

⇒ ⛔ **I due muri sono lo stesso muro**: senza Marionette non si accetta il certificato, e senza
certificato accettato non c'è pagina. **Mi fermo qui e lo dichiaro**, come dice la regola: due
tentativi, poi si passa.

### ⭐ CHE COSA RESTA DA FARE, e la strada corta non ha bisogno di Marionette

⭐ **La forma del banco è giusta e adesso è anche dimostrata**: il *prima* e il *dopo* sono **due
file `pagina.html`** serviti dallo **stesso binario** (`md5 162d2d10…`), e il `md5` della pagina si
legge nel registro (`d387c166…` per il vecchio, `e010d615…` per il nuovo). Il verbale lo manda la
**pagina stessa** ogni 5 s.

⇒ **Basta che la pagina si apra e si entri.** Due strade, in ordine di costo:

1. ⭐⭐ **Nic apre la pagina col suo browser** (`https://192.168.0.2:7920/`, utente `prova2`),
   accetta il certificato come fa sempre, e il registro del server porta i tre contatori
   `vecchi` · `tardivi` · `fuori` da sé. ⛔ **Non serve nessuno strumento nuovo**;
2. ⚠ Oppure si toglie il certificato di mezzo prima del browser: `cert_override.txt` nel profilo,
   o un certificato che il profilo già conosce. `[?]` **Non provato.**

⛔ **Finché non succede una delle due, la cura 4 (il riordino dell'audio) resta NON VERIFICATA**, ed
è l'ultima delle sei cure del 23 agosto senza un numero.

---

# §15 · ⛔ COM'È RIMASTA LA MACCHINA — *verificato alle 14:56 UTC, non dichiarato a memoria*

| | |
|---|---|
| `tc` su **`lo`** | ⭐ `qdisc noqueue 0: root` — **nessuna disciplina** |
| `tc` su **`enp7s0`** | ⭐ `qdisc mq 0: root` — **mai toccata**, come da regola |
| il **guardiano** di `tc` | ⭐ nessuno: `.b68-guardiano.pid` non c'è |
| **scene, clienti, browser** | ⭐ **nessuno** — né `04-b30-scena`, né `01-b3-cliente`, né `firefox` |
| **porte** | ⭐ **7900 · 7910 · 7920**, le tre di prima, nessuna in più |
| ⚠ **e alle 15:0x una QUARTA** | ⛔ **`7932` — NON è mia.** È comparsa **dopo** che avevo finito, insieme a `banchi/09-b78-apertura.py` sul portatile: è il banco di **un altro agente**. ⭐ Non l'ho toccata. ⚠ La scrivo perché «la macchina è rimasta così» invecchia male: ⛔ **i numeri di §14 non ne sono sporcati** — l'ultimo controllo `pulizia()` di ogni mio giro, fino alle 14:52:35, elencava **solo 7900 · 7910 · 7920** |
| **`core_pattern`** | `/media/REMOTIX/tmp/09c/core.%e.%p.%t` — **lasciato**, è la trappola armata di §4.7 |
| ⭐ **il registro della sera** | salvato in `/media/REMOTIX/tmp/09c/registro-fase9-sera-PRIMA-DI-B74.log` (9 216 437 byte) ⛔ **prima** che `09-b74` cancellasse `registro.log`: senza quella copia i numeri di §14.2-§14.6 non sarebbero più rileggibili |

⭐ **E la 7920 è tornata esattamente com'era**, verificato sulle righe che scrive lei stessa:
binario `md5 162d2d10…` (`f90eb21`), pagina **`md5 e010d615…`** (quella del prodotto, non quella
del *prima* dell'audio), **soglia della coda 0 ms (SPENTA)**, **regolatore SPENTO**, trappola glibc
spenta, fuori da ogni sessione utente.

⚠ **Quel che ho cambiato e non rimetto, perché è il lavoro**: `banchi/01-b3-cliente.py` adesso
negozia **H.264** (§14.1). ⛔ È il metro nuovo, e chi rilegge un numero vecchio deve guardare
**quale codec** dice il registro di quel giro.

---

## §16 · ⭐⭐⭐ IL CASO DURO SUL PERCORSO VERO — *23 agosto 2026, 15:20-15:30, col browser dell'utente*

⛔ **La prima misura della fase presa con un browser vero, sulla tela vera, sulla rete vera.** Tutte
quelle di prima venivano dal cliente di prova su `lo`.

**La scena**: un filmato di **grana pura** 2560×1080 a 30/s (`ffmpeg noise=alls=40:allf=t+u`, CRF 32,
90 s in ciclo), riprodotto con `mpv --fullscreen` dentro la sessione di `prova` sulla **7920**
(prodotto di `f90eb21`+, **nessun interruttore acceso**, tetto di banda SPENTO). Il client è
**Chrome** dell'utente da 192.168.0.3. ⇒ È il caso peggiore che un desktop possa produrre.

### 16.1 ⭐⭐ La banda: **21,5 – 23,1 Mbit/s**, cioè il **107-115 %** del pavimento

| | kbit/s | fotogrammi in 10 s | il più grosso |
|---|---|---|---|
| `[M]` 15:2x | **21 542** | 306 | 365 133 byte |
| `[M]` 15:2x | **23 092** | 299 | 355 169 byte |

⛔ **E questo corregge §14.2 nel verso che conta**: il banco, con la sua scena sintetica, dava
**44,574 Mbit/s = 223 %** del pavimento. Il caso duro **vero** ne chiede **la metà**.
⇒ ⭐ **Il tetto di banda serve ancora — ma il margine da recuperare è di 2-3 Mbit/s, non di 25.**
⚠ E resta `[?]` **quanto sia duro il caso più duro possibile**: la grana pura è un limite superiore
sintetico anche lei; un film vero comprime meglio.

### 16.2 ⭐⭐⭐ E il prodotto TIENE, senza nessuna cura accesa

`[M]` dal verbale che la pagina manda da sé ogni 5 s, e dal registro del figlio:

| | |
|---|---|
| fotogrammi | **7 125 consegnati → 7 125 dipinti** · `salt 0` · `buchi 0` · `ord 0` |
| chiavi | ⭐ **1** in tutto il giro |
| audio | **35 169 ricevuti → 35 169 suonati** · `vecchi 0 · tardivi 0 · fuori 0 · rec 0 · dop 0` |
| coda audio | 238 ms |

⇒ ⛔ **Nessuna spirale, nessun abbandono, nessuna degradazione** — a **interruttori tutti spenti**,
sul caso peggiore, appena sopra il pavimento. ⭐ È la conferma più forte che la fase 9 potesse
ricevere sul verso della decisione §3.1-bis: **a 20 Mbit/s il prodotto non ha bisogno di degradare.**

### 16.3 ⭐ La cura del riordino audio (cura 4): **inerte sul percorso dell'utente, come previsto**

`[M]` `vecchi 0 · tardivi 0 · fuori 0` sia a riposo (4 936/4 936) sia sotto il caso duro
(35 169/35 169). ⇒ ⭐ **La metà che conta per il prodotto è dimostrata**: la cura **non ha cambiato
niente per l'utente**. ⚠ **La metà che morde — la purezza sotto riordino ≥ 0,95 — resta `[?]`**: si
può fare solo sporcando `enp7s0`, che è l'interfaccia dell'ssh e della sessione dell'utente, e non
è stata toccata.

### 16.4 ⛔⛔ LA DESINCRONIA AUDIO-VIDEO CRESCE SOTTO CARICO — ma **NON è giudicabile a occhio**

`[M]` il campo `AV` del verbale della pagina: **+331 ms** a riposo → **+690 ms** sotto il caso duro.
⇒ Il suono precede l'immagine di quasi **sette decimi di secondo**.

⛔ **E qui il banco è stato l'occhio dell'utente, per due volte, e ha detto NO:**

> *«non posso sapere se c'è disallineamento se il video è incomprensibile»* — sulla grana pura, che
> non offre **nessun riferimento** fra quel che si vede e quel che si sente.
>
> *«ancora difficile giudicare il sync»* — sulla stessa scena con un **riferimento innestato**: tutto
> lo schermo lampeggia in bianco per 0,12 s **una volta al secondo**, e nello stesso istante c'è un
> **bip** (`sine=frequency=440:beep_factor=4`).

⛔ **Due letture, e vanno tenute tutt'e due invece di scegliere quella comoda:**

| | |
|---|---|
| ⭐ **una desincronia che non si riesce a giudicare è una desincronia che non morde** | ed è il metro del prodotto: `LEZIONI.md` §7.3, *«quando l'utente dice che va bene, va bene»* |
| ⛔ **oppure lo STRUMENTO non serve, e allora il numero non è ancora stato messo alla prova** | 690 ms su un lampo a schermo intero **dovrebbero** vedersi. Se non si vedono, o `AV` non misura quel che crediamo, o il lampo si perde nella grana, o il bip non cade dove credo |

⇒ ⏳ **Resta `[?]`, e la strada è una misura OGGETTIVA, non un altro giro d'occhio**: un riferimento
che si possa **leggere** invece che giudicare — un lampo su fondo **calmo** (non grana), catturato
insieme al suono, e i due istanti confrontati sul filo. ⛔ E prima di misurarlo va **certificato lo
strumento**: `AV` va confrontato con un ritardo **noto e innestato**, o è un numero che nessuno ha
mai verificato. ⚠ È la stessa forma di `DECISIONI.md` §7.19, dove la desincronia ~400 ms è aperta
**da agosto** e non è mai stata chiusa.

⚠ **E un difetto del metodo, dichiarato**: la scena di prova era **grana pura**, cioè il caso in cui
l'occhio ha **meno** appigli possibili. Chiedere un giudizio di sincronia lì è stato un errore mio,
e la seconda scena non l'ha corretto abbastanza.

### 16.5 Che cosa resta acceso

`[M]` la scena e `mpv` **fermati** alle 15:30. I due filmati restano in
`/media/REMOTIX/tmp/09-scena/` (`duro.mp4` 209 MB, `duro-sync.mp4` 208 MB) — ⚠ su NVMe, **non** sul
rootfs in RAM: il primo tentativo li aveva scritti in `/home/prova`, che vive in RAM, e a CRF 18
faceva **4,1 GB**. Cancellato subito.
⚠ Installati sulla macchina `mpv` e `ffmpeg` (il rootfs vive in RAM: dopo un riavvio vanno rimessi).
⛔ **Firefox sulla macchina di prova NON parte** per l'utente `prova`: il profilo non viene mai
creato (`~/.mozilla/firefox/` ha solo `Crash Reports` e `Pending Pings`). È lo stesso muro su cui si
è fermato il banco dell'audio. ⏳ Non diagnosticato.

---

# §17 · ⭐⭐⭐ LA RETE CATTIVA — *23 agosto 2026, sera*, e **il bersaglio della fase è stato corretto dal regista**

> *«Comunque voglio farti notare una cosa: 30 mbps sono una connessione da metà anni 90. La vera
> sfida è misurare performance con reti che perdono pacchetti o pacchetti fuori sequenza, o
> presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**, `PIANO.md` fase 9.

⛔ **E la correzione arriva a fase mezza misurata, con la prova che serviva.** §16 aveva appena
mostrato che sul **percorso vero** il caso peggiore chiede 21,5-23,1 Mbit/s e il prodotto lo regge
**senza degradare e con tutte le cure spente**: 7 125 consegnati → 7 125 dipinti, **una** chiave,
zero abbandoni. ⇒ Un banco che non riesce a far cedere quel che misura **non sta misurando la
grandezza giusta**. Le pagine che seguono sono la grandezza giusta.

## 17.0 ⛔ Le tre grandezze non sono la stessa cosa — e confonderle è il modo facile di misurare male

| | che cos'è | che cosa tocca da noi |
|---|---|---|
| **perdita** | il pacchetto non arriva | il **video** va su stream QUIC, che ritrasmettono ⇒ `[?]` si dovrebbe pagare in **ritardo**, non in fotogrammi. L'**audio** va su datagram ⇒ si paga in **buchi** |
| **fuori sequenza** | arriva, ma dietro a uno più nuovo | ⭐ è la condizione mancante della **cura del riordino dell'audio** del 23 agosto, l'unica cura della giornata la cui metà utile non era mai stata verificata |
| **jitter** | arriva a intervalli irregolari | `[?]` QUIC può **scambiarlo per perdita** e stringere la finestra senza motivo. Se succede, il calo è **nostro** |

⭐ **E il `netem` su `lo` è diventato una risorsa unica con un lucchetto** (`banchi/09-lucchetto.py`):
la disciplina si mette sulla **radice** dell'interfaccia, quindi due banchi che guastano insieme
non si dividono il lavoro — **il secondo cancella il guasto del primo, e il primo continua a
misurare credendo di averlo**. ⚠ Non darebbe rosso: darebbe un numero plausibile. Il possesso si
prende con `mkdir` (atomico anche su ssh), porta una **scadenza scritta dentro**, e chi scassina un
lucchetto scaduto **lo dichiara**.

## 17.1 ⛔⛔⛔ IL VIDEO — la griglia, e **non è una degradazione: è un dirupo**

`banchi/09-b76-rete-cattiva.py` · `[M]` 23 agosto 2026 · 25 s per profilo · 1920×1080 · h264 ·
**banda libera** · ⛔ **tutte le cure ai predefiniti, cioè SPENTE** · binario `51b5994`.

| profilo | persi % (sonda) | raffica | fuori ord. % | **fps** | peggior s | chiavi/tot | deriva max | Mbit/s sul filo |
|---|---|---|---|---|---|---|---|---|
| `liscio` | 0,00 | – | 0,0 | **39,97** | 38 | 0/878 | 6 ms | 3,18 |
| `ritardo-30` ⭐**rif.** | 0,00 | – | 0,0 | **40,11** | 37 | 0/881 | 1 ms | 3,13 |
| `perdita-0,5` | 0,36 | 1,00 | 0,0 | **40,06** | 37 | 0/881 | 46 ms | 3,14 |
| ⛔ `perdita-1` | 0,94 | 1,01 | 0,0 | **9,56** | 4 | 117/209 | 142 ms | 4,00 |
| ⛔ `perdita-3` | 2,96 | 1,03 | 0,0 | **4,03** | 2 | **87/87** | 180 ms | 2,56 |
| ⚠ `perdita-5` | 4,78 | 1,04 | 0,0 | **3,35** | 2 | 73/73 | 157 ms | 2,01 |
| ⭐ `raffica-1` | 1,07 | **6,14** | 0,0 | **23,94** | **0** | 38/526 | **3 707 ms** | 2,99 |
| ⛔⛔ `raffica-forte` | 13,03 | 5,03 | 0,0 | **sessione STACCATA a 0,3 s su 25** | – | – | – | – |
| ⭐ `riordino-25` | 0,00 | – | **68,0** | **40,03** | 38 | 0/880 | 11 ms | 3,27 |
| `jitter-5` | 0,00 | – | 85,3 | **39,30** | 32 | 2/864 | 17 ms | 3,52 |
| ⛔ `jitter-15` | 0,00 | – | 86,3 | **16,62** | 4 | 102/364 | 312 ms | **6,93** |
| ⛔ `jitter-30` | 0,00 | – | 73,2 | **8,07** | 2 | 110/175 | 475 ms | **6,26** |
| `duplicazione-1` | 0,00 (1,02 % dup) | – | 0,0 | **39,96** | 37 | 0/878 | 2 ms | 3,20 |
| ⛔ `casa-cattiva` | 1,71 | 1,02 | 93,8 | **7,78** | **0** | 73/169 | 609 ms | 3,51 |

⛔ **Tredici predicati rossi**, e nessuno muto. Il guasto è stato **verificato messo** su tutti e 14
i profili, con **due gambe che concordano**: il `dropped` del qdisc e una sonda indipendente
(`[M]` `loss 5%`: `dropped 101`, sonda 101 su 2000).

### 17.1-bis ⭐⭐ Le tre cose che i numeri dicono, e nessuna era attesa

1. ⛔⛔ **C'è un dirupo dentro il primo punto percentuale di perdita**: dal 100 % del riferimento al
   **24 %**. Non è una curva, è un **gradino**. ⚠ E nessuna prova di banda l'avrebbe mai trovato: a
   `perdita-1` il filo porta **4,00 Mbit/s**, cioè il **20 % del pavimento dichiarato**. La linea è
   vuota, e il prodotto è in ginocchio.
   ⛔ ⚠ **La forbice «0,36 %-0,94 %» che questa riga portava è SBAGLIATA, e §17.11 la ritira**:
   nasceva da una casella (`perdita-0,5` a *40,06 · zero chiavi*) che **non si riproduce**.
2. ⭐⭐⭐ **A `jitter-15/30` il filo porta il DOPPIO dei byte (6,9 contro 3,1 Mbit/s) per UN QUINTO
   dei fotogrammi, su una rete che non perde un pacchetto.** `[M]` perdita misurata **0,00**.
   ⇒ È la prova diretta che **il disordine viene scambiato per perdita**: ritrasmissioni e chiavi
   che nessuna perdita ha chiesto. Il calo **è nostro**, non della rete — e §3.1-ter lo aveva
   scritto come `[?]` prima di misurarlo.
3. ⚠ **La stessa perdita media fa MENO danno a grappoli che sparsa**: `raffica-1` (1,07 %, grappoli
   da 6) tiene 23,94/s contro i 9,56/s di `perdita-1` (0,94 %, uno alla volta). ⛔ **Ma il prezzo si
   sposta e peggiora**: un secondo intero a **zero fotogrammi**, e la deriva a **3,7 secondi**.

### 17.1-ter ⭐⭐ IL MECCANISMO — letto nel registro del server, non dedotto

`[M]` sugli stessi giri: `abbandonato_in_coda` = `abbandonati` = `chiave_aspetta` **a ogni profilo
rosso** (129 · 102 · 116 · 125 · 83), con `delta_non_spedito` a 550-800. E i **buchi nella
successione dei `numero`** — la seconda gamba, contata dal lato che riceve e indipendente dal
registro del server — concordano: 116, 86, 102, 109, 72.

⇒ **La catena è la spirale di §5.1→§5.2**, ed è la stessa faccia del difetto del 21 agosto:

> il filo ritarda → la coda di spedizione cresce → §5.1 abbandona i delta → §5.2 accende il debito
> → si chiede una **chiave** → la chiave riempie la finestra → **ricomincia**

⛔ A `perdita-3` fa **87 chiavi su 87 fotogrammi**: identica al 144/144 del 21 agosto.

⭐⭐ **E la cura di questa catena era già scritta, collaudata e SPENTA** — `--sgombra-soglia-ms` e
`--ritmo-adattivo`, dietro interruttore per l'invariante I6. ⇒ La griglia qui sopra è girata **con
gli interruttori spenti**, ed è la ragione per cui la prova appaiata delle cure (§17.6) è il
seguito obbligato di questa pagina e non un di più.

### 17.1-quater ⛔⛔ `raffica-forte` — **NESSUNO si stacca: si ferma la CONSEGNA**

⚠ La prima lettura di questa casella diceva *«la sessione muore dopo 0,3 s su 25»*. ⛔ **La parola
era sbagliata, e una parola sbagliata su un rosso è peggio di un rosso mancato**: manda a cercare la
causa dove non è — qui, un congedo che non esiste.

`[M]` 23 agosto, **quattro testimoni** (`banchi/09-b79-cure.py`): il cliente stampa *«ancora
attaccato dopo 25,0 s: niente è caduto»* e chiude **lui** a fine finestra · l'audio arriva per tutto
il giro (**696 datagram, purezza 1,0000**) · il registro del server non ha **nessun** `CONGEDO`,
nessun `posto NEGATO`, nessun ban · la sessione si era aperta normalmente (`AMMESSO dopo 1 837 ms`),
il che esclude anche *«la stretta di mano non si completa»* — coerente con §17.4. `IDLE_MS` è
30 000 ms e infatti non c'entra.

⇒ **A fermarsi è la sola consegna dei fotogrammi**: `[M]` **121 spediti su 981 catturati, 860 NON
SPEDITI**, con `cwnd` inchiodata a **~10 KB** e il pacer che rifiuta.

⛔ **Il fatto resta grave, e non va declassato**: una sessione **viva e muta** è uno schermo fermo, e
per chi guarda è indistinguibile da un filo caduto. ⚠ Ma ha **un altro nome e un'altra causa** — non
viola *«mai staccare»*, viola il pavimento della scala (`DECISIONI.md` §2.1: 25 fotogrammi/s).
⇒ Il predicato `p_niente_stacco` di `09-b76` misurava **quanto è durata la consegna**, non **se la
connessione è caduta**: il numero era giusto, la parola no. ⏳ In cura: il predicato si spezza in
due, perché sono due fatti con due cause.

⭐⭐ **E le cure lo cambiano**: in B e in C la consegna dura **tutti i 25 secondi** (§17.6).

## 17.2 ⭐⭐⭐ L'AUDIO NEL RIORDINO — **la cura morde**, e adesso è misurato

⛔ Era la sola cura del 23 agosto la cui metà utile fosse rimasta `[?]`, e per una ragione detta:
*«per verificarla bisogna sporcare la rete e non l'ho fatto»*. La correzione del regista **è la
condizione mancante di quella verifica**.

⛔ **E prima è stato necessario portare la cura nel cliente dei banchi**: era stata scritta **solo
in `src/pagina.html`**, mentre `banchi/01-b3-cliente.py` aveva ancora la regola vecchia. ⇒ Fino a
stasera **nessun banco poteva misurarla**. Adesso c'è `--audio-regola vecchia|nuova`, ⛔ col
predefinito **`vecchia`** e la verifica che con quello i contatori e la **lista** dei blocchi
consegnati sono identici a una trascrizione letterale del codice del 22 agosto su cinque
successioni: un cliente che cambia i numeri già scritti non è uno strumento, è una variabile.

`banchi/09-b77-audio-riordino.py` · `[M]` 23 agosto 2026 · porta 7931 · 25 s per giro · **due giri
identici in tutto tranne la regola**:

| profilo | regola | **PUREZZA** | tono | copertura | sul filo | conseg. | vecchi | fuori | rec | dop | srv `dgram_falsi` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `liscio` | vecchia | 1,0000 | 1,000 | 1,0000 | 4993 | 4993 | 0 | 0 | 0 | 0 | 0 |
| `liscio` | **nuova** | 1,0000 | 1,000 | 1,0000 | 4992 | 4992 | 0 | 0 | 0 | 0 | 0 |
| `jitter-2` | vecchia | 0,7992 | 0,804 | 0,7993 | 4989 | 3987 | **1002** | 0 | 0 | 0 | 1062 |
| `jitter-2` | **nuova** | **1,0000** | 1,000 | 0,9982 | 4983 | 4983 | 0 | 1028 | 1028 | 0 | 115 |
| `jitter-5` | vecchia | 0,6877 | 0,683 | 0,6854 | 4970 | 3418 | 1552 | 0 | 0 | 0 | 698 |
| `jitter-5` | **nuova** | **1,0000** | 0,995 | 0,9954 | 4970 | 4970 | 0 | 1620 | 1620 | 0 | 732 |
| `jitter-15` | vecchia | 0,4350 | 0,370 | 0,3670 | 4214 | 1833 | 2381 | 0 | 0 | 0 | 1458 |
| `jitter-15` | **nuova** | **1,0000** | 0,846 | 0,8361 | 4177 | 4177 | 0 | 2392 | 2392 | 0 | 1458 |
| `riordino-25` | vecchia | 0,8912 | 0,895 | 0,8912 | 4990 | 4447 | 543 | 0 | 0 | 0 | 1415 |
| `riordino-25` | **nuova** | **1,0000** | 1,000 | 0,9982 | 4982 | 4982 | 0 | 550 | 550 | 0 | 450 |
| `casa-cattiva` | vecchia | 0,4013 | 0,261 | 0,2585 | 3192 | 1281 | 1911 | 0 | 0 | 0 | 1190 |
| `casa-cattiva` | **nuova** | **1,0000** | 0,648 | 0,6264 | 3120 | 3120 | 0 | 1837 | 1836 | 0 | 1190 |

**Sei profili su sei verdi, zero rossi, zero non giudicati.** `doppioni` **0** dappertutto (un
doppione qui vorrebbe dire che l'ha spedito il server); `scartati_tardivi` **0** dappertutto (la
rete di sicurezza dopo il decodificatore non ha mai dovuto scattare); `recuperati` ripaga i
`mancati` **uno a uno** (1028/1028, 1620/1620, 2392/2392) — cioè la cura **non si accusa da sola**
di perdite che ha invece recuperato.

⭐ **E la cura resta onesta**: `--certifica` porta due casi che le darebbero **rosso** se lo fosse —
purezza 0,999 **con** `fuori_ordine` a zero (vorrebbe dire che il profilo non morde e il verde è un
caso), e la controprova che la regola nuova **butta comunque** il blocco arrivato davvero troppo
tardi. Una cura che tenesse tutto non sarebbe una cura: sarebbe la rimozione di un controllo.

### 17.2-bis ⛔⛔ IL `[M]` DEL «0,175» — il conteggio regge, **la sua purezza no**

`src/pagina.html` · `avvia_audio()` portava: *«jitter ±2 ms ⇒ purezza 0,175, 1 004 scartati su 4 989»*.
`[M]` stasera, stesso profilo: **1 002 buttati su 4 989 sul filo**. ⇒ Lo **stesso denominatore**,
due blocchi di differenza: il **conteggio** di quel `[M]` è solido.

⛔ **Ma la sua «purezza 0,175» non è confrontabile con niente**, ed è stato fermato prima che
diventasse un trionfo. La frazione che usano i banchi della pagina è `suonati/ricevuti`
(`09-b74:300`), e `a.ricevuti++` sta **dopo** i rami di scarto (`pagina.html` · `avvia_audio()`): il denominatore
conta **solo i sopravvissuti**, quindi quel rapporto vale ~1,000 **con tutt'e due le regole**, su
una successione anche distrutta. ⚠ È vero nel codice **prima** e **dopo** la cura, verificato su
`f90eb216^`: da dove venisse quello 0,175 **non si sa**, ed è un numero di cui non si conosce la
definizione.

⭐ ⇒ La grandezza del banco è **`purezza = consegnati / sul filo`**, col denominatore contato
**prima** del vaglio, e l'atteso è un **confine dichiarato** (0,90 / 0,80 / 0,60), non quel punto.
`purezza_pagina` si stampa accanto **solo per confronto**, con scritto che è cieca.

### 17.2-ter ⛔⭐ IL ROSSO CHE ERA DEL BANCO — e la cura del predicato

`casa-cattiva` dava rosso: il cliente contava **2 183 `mancati` su 4 996, il 43,7 %**, con `netem`
al **2 %**. ⛔ Non era la rete: il registro del server diceva **1 823 blocchi RIFIUTATI da ngtcp2** —
mai messi sul filo, finestra di congestione chiusa a 40 ms di ritardo. `mancati` si costruisce sui
salti di `istante`, e **un blocco mai spedito lascia lo stesso salto di uno perso**.

⇒ Il predicato è stato riscritto **sui due capi**: `spediti dal server − sul filo del cliente` =
**67 perduti sulla rete, il 2,10 %**, contro il 2 % chiesto a `netem`. ⭐ È R13 in forma pura — un
numero che sembrava misurare la rete e misurava noi.

### 17.2-quater ⚠⚠ E DIETRO C'È UN FATTO DEL PRODOTTO CHE NON C'ENTRA CON LA CURA

`[M]` i blocchi audio **rifiutati da ngtcp2**, cioè prodotti e mai messi sul filo: **4** su
`jitter-2`, **819** su `jitter-15`, **1 823** su `casa-cattiva` — ⛔ **il 36 % dell'audio prodotto
non raggiunge il filo**. ⇒ È anche il motivo per cui su `jitter-15` e `casa-cattiva` la *copertura*
resta 0,84 e 0,63 **pur avendo purezza 1,0000**: il ricevente consegna tutto quel che gli arriva,
ma **il trasporto non gli fa arrivare tutto**. ⏳ Aperto, e non è un difetto della cura: è la stessa
finestra di congestione che nel video produce la spirale.

## 17.3 ⭐⭐⭐ DUE TESTIMONI NUOVI NEL SERVER — e uno misura il RIORDINO

⛔ Prima di stasera il registro **non sapeva dire di chi fosse la colpa**. Un fotogramma in ritardo
poteva essere un pacchetto perso e rimandato, la finestra chiusa, noi che l'abbiamo tenuto o noi
che l'abbiamo abbandonato: le ultime due si contavano, **le prime due no**.

**1 · la riga `rete-quic`** (`src/webtransport.c`, `rete_ciclo()`) — al più una al secondo, e
**tace se i contatori sono fermi e il giudizio non è cambiato**:

```
rete-quic 192.168.1.9:52344 da_ms=1002 persi=7 persi_d=3 byte_persi=9856 ... cwnd=48000
cwnd_left=0 ssthresh=32000 involo=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400
min_rtt_us=22100 coda_rete_us=19130 pto_us=132000 dgram_persi=… giudizio=⛔ la linea perde
```

⚠ Tre scelte che un banco deve sapere: `giudizio=` è **l'ultimo campo** e il suo valore arriva a
fine riga; l'rtt è in **microsecondi** (in rete locale `rttvar` arrotondato ai ms varrebbe 0, e
nasconderebbe proprio il jitter che è il bersaglio); `da_ms` è l'intervallo **vero**, e i campi `_d`
valgono su quello — chiamarli `_1s` sarebbe stato un numero che sembra misurato e non lo è.

Il **giudizio** ha tre valori e la regola è scritta: `persi_d > 0` ⇒ `⛔ la linea perde` (per primo,
perché la finestra chiusa è quasi sempre la **conseguenza** della perdita, e invertendo la causa si
nasconderebbe dietro il suo effetto); altrimenti `cwnd_left == 0 && cwnd > 0` ⇒ `⚠ la finestra e'
chiusa`; altrimenti `-- niente da segnalare`. ⛔ Il giudizio **non parla di jitter né di riordino**,
apposta: quei numeri ngtcp2 non li dà, e dedurli da `rttvar` avrebbe voluto una **soglia**, cioè una
decisione.

**2 · ⭐⭐⭐ `dgram_falsi` — il riordino, misurato dal lato del server.**
`[S]` `ngtcp2.h:3442`, sul callback `lost_datagram`: *«Note that the loss might be spurious, and
DATAGRAM frame might be acknowledged later»*. ⇒ Stesso `dgram_id` visto prima come **perso** e poi
come **riscontrato** = pacchetto **arrivato fuori sequenza**, dichiarato perduto dalla soglia dei
tre pacchetti e riscontrato dopo.

⛔ Fino a stasera `ngtcp2_callbacks` (`src/trasporto.c` · `ngtcp2_callbacks`) registrava `recv_datagram` **e basta**:
i datagram in arrivo si contavano (rilievo B-10), quelli in **partenza** — cioè l'audio — sparivano
nel filo senza lasciare traccia. *«L'audio non è arrivato»* e *«è arrivato e il cliente l'ha
buttato»* avevano la stessa faccia, ed è lo stesso difetto di allora dall'altro verso.
⛔ E si registrano **in coppia**: `lost_datagram` da sola conterebbe i riordini come **perdite**,
cioè darebbe un numero **più alto del vero** e senza dirlo.

⚠ **Il prezzo, dichiarato**: vale **sui datagram soltanto**, cioè sull'audio. Gli stream QUIC non
hanno un identificativo per pezzo, e questa strada lì **non c'è** — sul video il riordino resta
senza testimone diretto.

### 17.3-bis ⛔ Quel che ngtcp2 1.25 NON dà, detto forte

- **i ritrasmessi non esistono** `[S]`: QUIC non ritrasmette pacchetti, ritrasmette i *frame*
  dentro pacchetti nuovi, e non c'è nessun contatore di rimandi. `pkt_lost` (i pacchetti
  **dichiarati** perduti) è quanto ci si avvicina;
- **il riordino sugli stream non si conta** `[S]`: nessun campo, nessun callback, e la soglia dei
  tre pacchetti ngtcp2 la usa al suo interno senza esporla. ⇒ Lì `rttvar` resta l'unico indizio;
- **`delivery_rate` non esiste** `[S]`: la banda resta stimata da `cwnd`/`smoothed_rtt`;
- ⛔ **il contatore `reordered` di `tc` non esiste su questa macchina** `[M]`: iproute2 6.15.0, il
  blocco `netem` stampa solo `Sent/dropped/overlimits/requeues/backlog`, e con `reorder 25% 50%`
  acceso si muove solo `requeues`. ⇒ Il riordino è stato misurato con **tre testimoni concordi** —
  una sonda UDP numerata attraverso lo stesso `netem`, i sorpassi contati sul JSONL del cliente, e
  `dgram_falsi` dal server — non dedotto.

## 17.4 ⭐⭐ LA STRETTA DI MANO SOTTO PERDITA — **il `[M]` del 10 % era un difetto del banco**

`banchi/09-b78-apertura.py` · `[M]` 23 agosto 2026 · 10 giri per gradino · perdita **letta** da
`tc -s qdisc` · fino ad `AMMESSO` (QUIC + CONNECT estesa + `CIAO/ECCOMI` + `CREDENZIALI/AMMESSO`):

| perdita chiesta | perdita vera | aperte | QUIC mediana | totale mediana | totale max |
|---|---|---|---|---|---|
| 0 % | – | **10/10** | 7,8 ms | 1 014 ms | 1 116 ms |
| 5 % | 8,2 % | **10/10** | 7,8 ms | 1 078 ms | 1 318 ms |
| 10 % | 9,5 % | **10/10** | 10,9 ms | 1 103 ms | 1 219 ms |
| 15 % | 15,2 % | **10/10** | 111,5 ms | 1 281 ms | 1 708 ms |
| 25 % | 24,3 % | **10/10** | 211,9 ms | 1 299 ms | 1 738 ms |

⭐ **La sessione si apre sempre**, anche al 25 %. **La rete costa 285 ms fra lo 0 e il 25 %**; il
secondo che si vede **non è la rete**, è il ritardo fisso di §4.4-bis contro chi prova le password.
I massimi della stretta di mano stanno a 212 e 613 ms — **uno e due PTO**.

Le cinque ipotesi, tutte smentite una per una: il cliente non si arrende (**0 giri su 70** hanno
superato il suo tetto di 8 s); il ban non c'entra (`src/rcp.c` · il conteggio dei verdetti PAM conta solo verdetti PAM su
`CREDENZIALI`, e una stretta di mano non ci arriva); ngtcp2 riprova (`handshake_timeout` resta
`UINT64_MAX`, `trasporto.c` · `accetta()`); il `netem` non è applicato due volte (i due filtri prendono i due
**versi**, quindi un **giro** paga `1-(1-p)²` e un **datagram**, che fa un verso solo, paga `p` —
`[M]` 3 235/3 607 = 89,7 %).

### 17.4-bis ⛔ IL PREDICATO CHE NON POTEVA DARE ROSSO — R13 di nuovo, in `07-b64-rete.py`

```python
def a_non_si_apre(n):
    return _p(n["ricevuti"] == 0, "nessun datagram: la sessione non si apre")
```

⛔ `01-b3-cliente.py` · `_capsula_chiusura()` stampa `[audio] ricevuti 0` **anche dal ramo `except`**, prima di
rilanciare. ⇒ **Ogni** modo di fallire — un `CONGEDO`, un tetto scaduto, un `NameError` del banco —
faceva passare quel gradino di **verde**. Il banco non misurava *«non si apre»*: misurava *«non ho
ricevuto»*, e le due cose hanno la stessa faccia.

⛔ **E un secondo difetto nello stesso file**: `guasta([])` chiama `rimetti(False)`, che chiama
`guardiano_disarma()`. Il profilo `0-liscio` è **il primo**, quindi disarmava il guardiano armato
due righe prima, e gli **otto profili successivi giravano senza rete di sicurezza**.

⏳ **Le due cure sono scritte e NON applicate**: `07-b64-rete.py` è importato dai banchi che stanno
girando in questo momento, e cambiargli una firma a metà misura sarebbe il difetto che questa
sezione descrive.

## 17.5 ⛔⛔ IL FANTASMA — *«hai già una sessione attiva altrove»*, e per l'utente è **falso**

⭐ È il fatto di prodotto trovato dietro §17.4, e sul bersaglio della fase.

L'unico modo in cui un'apertura fallisce davvero sotto perdita è `ATTACCA` → `CONGEDO(0x0F)
GIA_ATTIVA_REMOTA` (`[M]` 5/10 al 10 % di perdita). Il registro dice: *«posto NEGATO … lo occupa un
altro client di questo stesso utente»*.

⛔ **Il conto si chiude senza `netem`**, perché un addio **perso** e un addio **mai detto** sono lo
stesso fatto: ucciso il cliente con `-9`, `[M]` **11 rifiuti di fila, e il posto torna libero a
+30,5 s** — cioè `SILENZIO` (`src/rcp.c` · `SILENZIO`, 30 000 ms).

⚠ **La frase che il client costruisce è falsa per chi la legge**: quella sessione è **la sua**, ed è
morta un attimo prima. E il riquadro di `src/rcp.c:229-233` dichiara che quell'orologio *«fa
sparire il caso "il telefono è morto in galleria"»* — ⛔ non lo fa sparire: lo **dura trenta
secondi**, e la perdita di pacchetti è precisamente quel che lo rende **normale** invece che raro.

**La cura proposta, NON scritta — è un cambio di politica di §8.2 e la decide l'utente:** in
`src/rcp.c`, ramo `POSTO_OCCUPATO` di `rcp_attacca()` (righe 2605-2616), prima di congedare con
`0x0F` guardare l'`ultima_vita` dell'occupante: se tace da più di una soglia breve (~3 s) **mentre
un altro client dello stesso utente sta chiedendo il posto**, sfrattarlo. §8.2 dice *«nessun client
attaccato e **vivo** viene mai spodestato»* — l'occupante qui è attaccato ma **non vivo**, e oggi
l'unico orologio che lo distingue è quello da 30 s. `torna_a_parlare()` (`rcp.c` · `drena()`) gestisce già
lo sfrattato che torna. ⛔ Non toccherebbe `SILENZIO`, che resta 30 s per tutto il resto.

## 17.6 ⭐⭐⭐ LE DUE CURE, APPAIATE — **la spirale si spegne, e solo con tutt'e due**

`banchi/09-b79-cure.py` · `[M]` 23 agosto 2026 · binario `eee17f40…` dall'**albero di lavoro** ·
25 s per casella · 1920×1080 · h264 · un giro per casella. ⛔ Ogni braccio verificato dalle **righe
d'avvio del prodotto**, non dalla riga di comando (un interruttore che si crede acceso e non lo è
darebbe un appaiamento senza differenza, cioè un verde). Il guasto verificato dalla sonda a **ogni**
casella.

- **A** = i predefiniti, cioè **cure spente**. ⛔ Rimisurato, non ripreso da §17.1: quei numeri
  vengono da un altro binario e da un'altra ora.
- **B** = `--sgombra-soglia-ms 100` — la sola soglia sulla coda.
- **C** = `--sgombra-soglia-ms 100 --ritmo-adattivo` — soglia **più** regolatore del ritmo.

| profilo | br | fps | peggior s | **chiavi %** | deriva fin. | **deriva max** | Mbit/s filo |
|---|---|---|---|---|---|---|---|
| `ritardo-30` ⭐**sana** | A | 39,85 | 36 | 0,0 | 0,1 | 8,9 | 7,55 |
| | B | 40,19 | 37 | 0,0 | 0,2 | 5,8 | 7,60 |
| | C | 39,63 | 36 | 0,0 | 0,9 | 6,1 | 7,53 |
| `perdita-1` | A | 11,96 | 5 | **51,7** | −2,4 | 76,5 | 3,43 |
| | B | 32,13 | 17 | 6,4 | 23,2 | 107,8 | 4,84 |
| | **C** | **32,85** | 21 | **0,0** | −1,6 | 99,3 | 5,11 |
| `perdita-3` | A | 7,34 | 5 | **88,1** | −40,0 | 53,4 | 2,17 |
| | B | 20,63 | 11 | ⛔ 23,8 | 32,9 | 139,3 | 2,90 |
| | **C** | 19,63 | 11 | **0,2** | −62,2 | 165,7 | 2,79 |
| `jitter-15` | A | 10,76 | 6 | **59,2** | 11,7 | 102,1 | 3,48 |
| | B | 25,88 | 9 | ⛔ 12,8 | −65,7 | 64,0 | 8,06 |
| | **C** | 21,48 | 15 | **0,0** | 53,8 | 168,4 | 6,63 |
| `jitter-30` | A | 8,56 | 5 | **73,1** | 6,7 | 115,6 | 2,55 |
| | B | 20,25 | 10 | ⛔ 19,9 | −5,0 | 277,0 | 5,77 |
| | **C** | 16,68 | 12 | **0,0** | −116,0 | 180,8 | 4,96 |
| `casa-cattiva` | A | 8,28 | 3 | **72,0** | −71,5 | 295,3 | 2,21 |
| | B | 14,37 | 6 | ⛔ 33,6 | 152,7 | 238,4 | 3,01 |
| | **C** | 13,86 | 4 | **5,6** | 102,2 | 284,2 | 3,38 |
| ⚠ `raffica-forte` | A | *la consegna muore a **4,4 s** su 25* | | | | | |
| | B | 4,25 | **0** | 44,6 | 24,9 | **7 756** | 0,59 |
| | C | 4,18 | **0** | 4,4 | 2,1 | **4 521** | 0,78 |

### 17.6-bis ⭐⭐ I quattro fatti

1. ⭐⭐⭐ **La spirale si spegne — ma solo col braccio C.** La quota di chiavi passa da **51,7-88,1 %**
   a **0,0-5,6 %** su tutti e cinque i profili rossi. ⛔ **La sola soglia (B) non basta**: lascia
   12,8-33,6 % di chiavi in quattro profili su cinque.
   ⭐ **E il perché si legge nei contatori del server**: in C, su `raffica-forte`,
   `delta_non_spedito` **988 → 6** e `chiave_aspetta` **32 → 0**. La soglia smette di *buttare*, ma
   il debito di §5.2 continua ad **accendersi**; il regolatore lo previene perché il fotogramma
   **non parte affatto**. ⇒ È la conferma sperimentale dell'ordine obbligato dichiarato in §6: la
   soglia è il **prerequisito** del regolatore, non un'alternativa.
2. ⛔⭐ **La linea sana non paga niente** — ed era il predicato che valeva più di tutti.
   39,85 / 40,19 / 39,63 fps (un punto percentuale, dentro il rumore dichiarato del 5 %), **zero
   chiavi** in tutt'e tre i bracci, deriva finale 0,1 / 0,2 / 0,9 ms. ⇒ Le cure **non hanno un
   costo di regime**: sono mute finché non servono, che è precisamente quel che I1 pretende.
3. ⭐ **Il ritmo torna da 1,7 a 2,8 volte** su ogni profilo rosso. ⚠ E B dà quasi sempre **più**
   fotogrammi/s di C: ⛔ non sono «peggio e meglio», sono **più fotogrammi con più chiavi** contro
   **meno fotogrammi tutti delta**. Chi confrontasse la sola colonna dei fotogrammi/s sceglierebbe B
   e prenderebbe la spirale in casa.
4. ⭐⭐ **E i byte sul filo SALGONO** (3,48 → 8,06 Mbit/s a `jitter-15`): ⇒ **la linea non era satura,
   era sprecata.** È l'altra faccia di §17.1-bis punto 2 — lì il doppio dei byte per un quinto dei
   fotogrammi, qui il doppio dei byte per **il doppio** dei fotogrammi.

### 17.6-ter ⚠ IL PREZZO, e i due numeri si danno senza scegliere

**Deriva massima**, sui cinque profili ordinari: da **−38 a +161 ms** rispetto ad A (⭐ su
`casa-cattiva` e `jitter-15` il braccio B la fa perfino **calare**). **Zero sulla linea sana.**

⛔ **Su `raffica-forte` il prezzo esplode: 4,5-7,8 secondi.** Lì C **non è ovviamente meglio di A**:
è *un'immagine che si muove con cinque secondi di ritardo* contro *un'immagine ferma*. ⚠ Questo
documento dà i due numeri e **non sceglie**: la scelta fra immagine e ritardo è dell'utente
(`DECISIONI.md` §0.1, invariante I6), non di una misura.

## 17.7 ⛔ I DIFETTI DI BANCO TROVATI STASERA — tutti della forma «silenzio invece di rosso»

| dove | che cosa | esito |
|---|---|---|
| `07-b64-rete.py` | `a_non_si_apre` verde su qualunque modo di fallire | ⭐ **curato** e rifatto girare (§17.4-bis, §17.9-bis) |
| `07-b64-rete.py` | `0-liscio` disarma il guardiano per gli otto profili dopo | ⭐ **curato**, `[M]` guardiano ancora vivo dopo `guasta([])` |
| `07-b64-rete.py` | `spediti_dal_server` a `None`: `None == 0` è falso ⇒ verde su un giro in cui il capo del server non era stato letto | ⭐ **curato**: adesso è muto (§17.9-bis) |
| ⛔ `07-b64-rete.py` | la riga di «conto finale» arriva **29 s tardi** quando il pacer ha coda ⇒ il giro dopo legge **il conto del giro prima** — e il posto ancora occupato lo fa morire di `GIA_ATTIVA_REMOTA` | ⭐ **curato** con `registro_posato()` (§17.9-bis) |
| `09-b70-ritmo.py` | `sudo -S` copre solo il **primo** comando della catena ⇒ il lettore §11.1 non si scriveva | ⭐ **curato** con `catena_root()` (§17.9-ter) |
| `09-b70-ritmo.py` | un `< file` in coda **ruba lo stdin a `sudo -S`** ⇒ `righe_registro()` torna 0 in silenzio, e `attese_a_vuoto` diventa cumulativo dall'accensione — cioè la colonna su cui I1 decide se rifiutarsi di giudicare | ⭐ **curato**, `[M]` 1 604 del giro contro 4 041 cumulativi |
| `09-b70-ritmo.py` | `01-b4-validatore.py` non viene spedito dal terreno ⇒ giornale vuoto ⇒ **rosso a «non stacca» su una sessione viva da 797 fotogrammi** | ⭐ **curato**: il terreno lo verifica, il banco si rifiuta |
| `09-b76` | ⛔ `p_niente_stacco` misurava **la durata della consegna** e la chiamava **stacco** | ⭐ **spezzato in due** (§17.9-quater) |
| `09-b79-cure.py` | l'avvolgimento di `root()` saltava la cura del sottostante | ⭐ **curato**, e `[M]` **nessun numero era sporcato** (§17.9-sexies) |
| `09-b76` (in corso d'opera) | ⛔ **`tc qdisc change` è appiccicoso**: un `reorder` messo per un profilo restava acceso nei quattro dopo | curato: il banco **rilegge** la regola installata e dà rosso se porta un verbo non chiesto |
| `09-b77` (in corso d'opera) | le regex cercavano i nomi **interni** dei contatori mentre il cliente stampa altri nomi ⇒ `None` su tutto, nessun errore | curato, e `--certifica` ora prova le regex sull'**uscita vera** del cliente |
| `09-b77` (in corso d'opera) | `mancati` conta come perduti anche i blocchi **mai spediti** | curato: il predicato lavora **sui due capi** (§17.2-ter) |

## 17.9 ⭐⭐ LA TORNATA DELLE CURE AI BANCHI — *23 agosto, notte*, e ne sono usciti altri quattro

⛔ **Sette difetti di banco su nove trovati stasera, e tutti della stessa forma: «silenzio invece di
rosso».** Le cure sono state applicate e **ogni banco è stato rifatto girare**. Quel che segue è il
seguito, e vale la pena leggerlo perché **due dei quattro nuovi sono usciti facendo girare il banco
curato**, non leggendolo.

### 17.9-bis ⛔⛔ IL TERZO E IL QUARTO DI `07-b64-rete.py` — e il quarto è il più grosso

**Terzo.** `spediti_dal_server` a `None`: `conti_del_server` torna `{"esito": "NIENTE DA LEGGERE"}`,
e `None == 0` è **falso** ⇒ il gradino filava dritto al predicato. I predicati che non guardano il
server (`a_pulito`, `a_sorpassi`) davano **verde su un giro in cui il capo del server non era stato
letto affatto**. ⇒ Adesso è **muto**.

**Quarto — ⛔ e questo sporca i numeri, non solo i verdetti.**
`[M]` **la chiusura di una sessione è lenta quando il pacer ha coda**: il profilo al 10 % di perdita
ha impiegato **29 secondi in più** degli altri a scrivere la sua riga di «conto finale». ⇒ Il giro
**successivo** prendeva la sua `riga0` **prima** che quella riga esistesse, e `conti_del_server()`
leggeva **il conto del giro precedente**.

⭐ **La firma è inconfondibile**: `[M]` tre profili di fila hanno riferito gli **stessi identici
numeri** («spediti 4999 · rifiutati 3 · rimandati 7410»), che erano il conto del **primo** dei tre.
Il conto vero del secondo era **4 632**. ⇒ Il predicato nuovo ha dato **rosso su un denominatore
altrui** (4 152/4 999 = 0,831), mentre col denominatore giusto era 4 152/4 632 = **0,896**, verde.

⚠ **E lo stesso ritardo produce un secondo effetto, peggiore**: il gradino dopo è morto con
`CONGEDO 0x0F GIA_ATTIVA_REMOTA` — il posto del precedente era **ancora occupato**, ed è la
serratura di 30 s di **§17.5**. ⇒ **Un giro può fallire per colpa del giro prima**, e l'`[audio]
ricevuti 0` che ne usciva è **esattamente il numero che il vecchio `a_non_si_apre` avrebbe chiamato
verde**. ⭐ I due difetti di §17.4-bis e il fantasma di §17.5 si nutrivano a vicenda.

**La cura**: `registro_posato()` — si aspetta che il conto delle righe «conto finale» stia **fermo
3 s** prima di cominciare un gradino — e `conti_del_server(riga0, n0)` **pretende una riga sua**,
altrimenti resta muto.

**Il giro nuovo di `07-b64`** `[M]` 23 agosto, porta 7801, 25 s per profilo: **9 gradini · 0 rossi ·
0 muti**, e il controllo positivo (`--controllo-rosso`) dà rosso con uscita 1 — il verdetto sa
ancora fallire. ⭐ Il gradino al 10 % conferma il conto dei due versi: **4 077/4 504 = 0,905** contro
`1-p` = 0,901. **È `1-p`, non `1-(1-p)²`**: un datagram fa **un verso solo**.

### 17.9-ter ⭐ LE TRE CURE DI `09-b70-ritmo.py`, e il numero che dimostra la seconda

`sudo -S` che copre solo il primo anello ⇒ nuova `catena_root()`, un solo `sudo -S bash -c` con la
catena dentro. `[M]` il lettore di §11.1 adesso **si scrive davvero** (4 130 byte) e riduce
**794 fotogrammi** per giro; la forma vecchia sullo stesso comando dava `Permission denied`.

Il `< file` che ruba lo stdin ⇒ `righe_registro()` torna **`None`**, non 0, e la guardia sta dove il
numero **si consuma**. ⭐ **Il numero che dimostra la cura:**

| | riga di partenza | righe `ciclo:` | `attese_a_vuoto` |
|---|---|---|---|
| giro mosso | 327 | 21 | **1 607** |
| giro fermo | 3 711 | 21 | **1 604** |
| ⛔ forma vecchia (`riga0` = 0) | 1 | 49 | **4 041** |

⇒ Col difetto, il giro fermo avrebbe dichiarato **4 041 invece di 1 604** — **2,5 volte**, e in
salita a ogni giro. ⛔ Ed è precisamente la colonna con cui `p_I1` decide **se rifiutarsi di
giudicare**.

**E la premessa falsa di I1**: la gamba «zero abbandoni a scena ferma» ora è **condizionata alla
perdita letta dal `qdisc` installato**, non assunta zero. Con perdita > 0 il predicato **si rifiuta**
invece di accusare il prodotto (era il falso rosso di `casa-cattiva`).

**Quarta cura, trovata dal giro vero**: il lettore §11.1 non partiva perché `01-b4-validatore.py`
non è fra i file che `07-b64-terreno.sh porta` spedisce ⇒ giornale vuoto ⇒ il banco dava **rosso a
«non stacca» su una sessione viva da 797 fotogrammi**.

### 17.9-quater ⭐⭐ `09-b76` — IL NOME GIUSTO, e la griglia rifatta

`p_niente_stacco` è **spezzato in due**, perché sono due fatti con due cause:

- **`p_connessione_viva()`** — vale su **tutti** i profili (§3.3/§8.3, anche sotto il pavimento) e
  interroga i **testimoni della connessione**, non i fotogrammi: il cliente (*«ancora attaccato dopo
  N s»*) e il registro (`congedo motivo=`, `posto NEGATO`, ban), **col motivo stampato**. ⚠ La terza
  possibilità — *«non si è mai aperta»* — è **muta** per costruzione, non rossa.
- **`p_consegna_non_si_ferma()`** — copertura ≥ 0,90 dei secondi che hanno visto almeno un
  fotogramma, e ⛔ **nessun buco ≥ 1,0 s**, **coda compresa**. ⚠ La soglia 0,90 **non è nuova**: è la
  stessa che usava il predicato vecchio. **Il numero non cambia: cambia la parola, ed è tutta la
  cura.** Il buco di 1 s ha la sua ragione: §2.1 mette il pavimento a 25 fotogrammi/s, quindi un
  secondo a **zero** è fuori scala, non «un ritmo basso».
- ⚠ Prezzo dichiarato: `[M]` sui tredici profili sani il buco massimo va da **0,04 a 0,35 s**,
  contro **14,26 s** a `raffica-forte` — più di un ordine di grandezza di margine, **zero falsi
  rossi**, diagnosi compresi.

⭐ E `--certifica` porta ora il caso che aveva ingannato il banco: **lo stesso giro dà rosso sulla
consegna e verde sulla connessione**. 49 casi su 49.

**`raffica-forte`, col nome giusto e i numeri** `[M]` (sonda: **11,10 %** di perdita in 197 raffiche,
media 4,51, max 27): **nessuno ha staccato** — cliente attaccato per tutti i 25 s, zero congedi. A
fermarsi è la **sola consegna**: **7 secondi su 25** hanno visto un fotogramma, **14,26 s di schermo
fermo di fila**, 952 righe `FOTOGRAMMA NON SPEDITO`, `cwnd` mediana **8 948 B** contro **105 616 B**
del riferimento (**12 volte meno**), `cwnd_left` mediana **0**. ⭐⭐ **E il server lo dice da sé**:
`⚠ la finestra e' chiusa` su **10 righe `rete-quic` su 18** — è il testimone di §17.3 che dà la
risposta senza che nessuno debba dedurla.

### 17.9-quinquies ⛔⛔ E DUE GRIGLIE DELLO STESSO BANCO NON COINCIDONO — dichiarato, non lisciato

Il giro di `09-b76` rifatto stanotte **non riproduce** quello di §17.1 su due profili:

| profilo | §17.1 (binario `51b5994`) | giro nuovo (binario da HEAD) |
|---|---|---|
| `perdita-0,5` | 40,06 fps · 0 chiavi | ⛔ **19,27** fps · spirale rossa |
| `jitter-5` | 39,30 fps | **31,45** fps |
| `perdita-1` | 9,56 | 12,32 |
| `raffica-1` | 23,94 | 29,47 |

⛔ **Non lo liscio, e non scelgo quale sia buono.** Le differenze note fra i due giri sono almeno
tre — binario diverso (HEAD porta le righe `rete-quic`, cioè **una `registro_dice` in più al
secondo**), macchina **riavviata** in mezzo, e il terreno ricostruito. ⇒ `[?]` **Non so quale delle
tre.**

⭐ **Che cosa sopravvive comunque, perché non dipende dal punto esatto:** la forma è la stessa in
tutt'e due i giri — una linea sana a ~40 fotogrammi/s, un **dirupo** entro il primo punto
percentuale di perdita, la spirale di chiavi come meccanismo, e il jitter che morde **senza perdere
un pacchetto**. ⛔ Quel che **non** si poteva più dire era **dove** stesse il gradino.
⇒ ⭐ **Sciolta da §17.11**, e la risposta è più interessante della domanda.

### 17.9-sexies ⭐ LA RIVERIFICA DI `09-b79` — **nessun numero era sporcato**, e sono tre prove lette

`09-b79-cure.py` avvolgeva `RETE.root` invece della catena curata. ⚠ E **non bastava scrivere
`B70.root`**: quando b79 arriva, `B70.root` è **già** stato sostituito da `09-b76:416` con un
avvolgimento che a sua volta chiama `RETE.root`. ⇒ La catena si ricostruisce dai pezzi
(`RETE.rem(B70.catena_root(c))`), e se `catena_root` non c'è **il banco si ferma invece di
misurare**.

⛔ Ma i numeri di §17.6 **reggono**, e non per fiducia:

1. `[R]` **il difetto era ancora da riscuotere**: alle 19:00 `09-b70.root()` faceva ancora
   `return RETE.root(...)`; la cura è delle **19:41**, dopo. Avvolgere `RETE.root` era allora
   *identico*. Il difetto era **prospettico**;
2. `[R]` **la `riga0` c'era**: `09-b76` sostituiva già `righe_registro` con la sua, col redirect
   **dentro** `bash -c`. `[M]` E la firma nei dati lo conferma: su tutte e **36** le caselle
   `attese_a_vuoto` sta fra 1 973 e 2 156 — **costante, non in salita** (su `ritardo-30` A/B/C:
   2 015 / 2 006 / 2 016). Il cumulativo di b70 era 4 041 contro 1 604, **in salita**: qui non c'è;
3. `[R]` **il conto di un altro giro è strutturalmente impossibile**: `07-b64-terreno.sh` fa
   `: > registro.log` a ogni `accendi`, e questo banco **riaccende il server a ogni braccio**.
   `[M]` Controprova: nessuna coppia di caselle porta numeri identici dal registro, e tre caselle
   hanno detto «NIENTE DA LEGGERE» invece del numero del vicino — ⭐ prova che **nella finestra non
   c'era niente da rubare**.

⭐⭐ **E la divisione che conta**: `[R]` i predicati sulla spirale, sul ritmo e sulla linea sana
leggono **solo** dalla traccia §11.1 del cliente; dal registro vengono solo quattro numeri di
**corroborazione**. ⇒ *«la spirale si spegne solo col braccio C: 51,7-88,1 % → 0,0-5,6 %»*
**non passa dal registro**, e i cinque profili rossi non si rifanno.

**Rimisurato `ritardo-30` a tre bracci** — il predicato che vale più di tutti:

| braccio | fps | chiavi | deriva fine | deriva max |
|---|---|---|---|---|
| A | 39,94 | 0,0 % | 0,0 ms | 10,1 ms |
| B | 39,94 | 0,0 % | 0,2 ms | 11,0 ms |
| C | 39,32 | 0,0 % | −0,1 ms | 6,2 ms |

**S′ verde**, e regge il confronto con le 19:00 (39,85 / 40,19 / 39,63). ⭐ E le righe della spirale
del braccio A tornano **identiche** (`chiave_aspetta` 1, `delta_non_spedito` 5,
`abbandonato_in_coda` 1): **un numero cumulativo non si riproduce, questi sì.**

## 17.11 ⭐⭐⭐ DOV'È IL DIRUPO — *23 agosto, notte fonda*: **il gradino è DOPPIO**, e il prodotto è **bistabile**

`banchi/09-b80-dirupo.py` · **42 giri** · perdita **letta** da una sonda a **20 000 pacchetti** a
ogni casella (⛔ a 0,1 % otto pacchetti non misurano un decimo di punto) · denominatore girato in
**apertura e chiusura** (39,95 → 39,93, **0,1 %**: la macchina non è derivata) · macchina messa
ferma per nome prima di cominciare · cure spente per tutti e 42 i giri.

### 17.11-bis ⛔ Prima il metro, poi la misura — e il metro è grosso

⛔ **Non ha senso confrontare due giri se non si sa quanto vale il rumore fra due giri identici.**

| profilo | giri | escursione | semi-escursione |
|---|---|---|---|
| perdita **0,00 %** | 3 | 39,89-40,17 | **0,4 %** |
| perdita **0,50 %** | 3 | 28,16-36,70 | **14,8 %** |
| perdita **0,50 %** | 5 | 20,79-36,70 | **27,6 %** |
| perdita **0,75 %** | — | — | **46,6 %** |

⇒ La contraddizione di §17.9-quinquies vale il **35,0 %**: il rumore **non la spiega tutta, ma ne
copre i quattro quinti**.

⭐⭐ **E il fatto vero è qui**: la dispersione **cresce con la perdita** (0,2 → 8,5 → 23,8 → 46,6 %)
e **non col carico**. `[M]` la CPU è stata **3,7-4,7 %** in *ognuno* dei 42 giri, il carico 0,3-0,8
su 20 core. ⇒ L'ipotesi «macchina carica» è **esclusa**, e quel che resta è del prodotto:

> ⛔⛔ **vicino al bordo la spirale è BISTABILE.** `[M]` a **0,20 %** di perdita, stesso binario,
> stesso terreno, a venti minuti di distanza: **`0 chiavi · 40,16/s`** e **`24 chiavi · 33,84/s`**.

⇒ Non è una soglia: è un **punto di biforcazione**. Lo stesso ingresso dà due uscite, e quale delle
due dipende da come è andata la prima manciata di secondi.

> ⛔⭐⭐ **«BISTABILE» È LA PAROLA SBAGLIATA, e la correzione è in §21.2** — *24 agosto*. Non sono due
> rami fra cui il prodotto sceglie: è **un innesco a senso unico**, con una probabilità **costante**
> ogni secondo. I giri da 25 s non erano una moneta lanciata sul prodotto: erano **una moneta
> lanciata su quanto a lungo avevamo guardato**.

### 17.11-ter ⭐⭐⭐ IL GRADINO È DOPPIO, e le due metà stanno lontanissime

| | dove casca | che cos'è |
|---|---|---|
| **il MECCANISMO** — la spirale di chiavi (§3.3) | ⛔ fra **0,00 % e 0,10 %** di perdita vera, **su tutt'e due i binari** | cioè **al primo pacchetto perso** |
| **il SINTOMO** — sotto il pavimento di 25/s (§2.1) | fra **0,53 % e 0,75 %** (HEAD) · fra **0,27 % e 0,47 %** (`51b5994`) | cioè **cinque volte più in là** |

⛔⛔ **Questa è la scoperta, e cambia il modo di leggere tutta §17.1**: il difetto **non comincia
dove si vede**. Fra il primo pacchetto perso e il momento in cui l'utente se ne accorge c'è mezzo
punto percentuale di perdita in cui **il prodotto sta già degenerando in chiavi** — e la degradazione
è già *nello spazio e nel tempo insieme*, che §3.3 vieta — **mentre i fotogrammi al secondo dicono
ancora che va tutto bene**.

⇒ ⭐ **Un banco che avesse guardato solo i fotogrammi/s avrebbe dato verde fino allo 0,5 %.** La
colonna che dà l'allarme cinque volte prima è **la quota di chiavi**, ed è la ragione per cui §17.1
la porta accanto ai fotogrammi/s invece che al posto loro.

**La griglia fine (HEAD)** `[M]`:

| perdita vera | fps | chiavi | peggior secondo |
|---|---|---|---|
| 0,000 % | 39,95 | **0** | 37,5 |
| 0,100 % | 39,44 | 2,5 | 23,5 |
| 0,195 % | 37,00 | 12 | 21 |
| 0,253 % | 34,83 | 20,5 | 5 |
| 0,532 % | 27,29 | 48 | 4 |
| **0,748 %** | ⛔ **13,50** | 101,5 | 4 |
| 0,998 % | 7,23 | 119,5 | 3,5 |
| 1,475 % | 5,52 | 112,5 | 3 |

⭐ **E niente si è mai staccato, e la consegna non si è mai fermata** — copertura 1,00 e buco massimo
≤ 0,37 s **ovunque**, nemmeno a 1,5 %. ⇒ Il divieto di §3.3 regge; a cedere è la scala, non il filo.

### 17.11-quater ⛔ La forbice del primo giro è ritirata, e il binario non c'entra

**La forbice «0,36-0,94 %» di §17.1-bis è sbagliata** e §17.11 la ritira. Nasceva da un
`perdita-0,5` che aveva dato *40,06 fotogrammi/s con **zero** chiavi*. `[M]` **In 7 giri a ~0,5 % di
perdita vera, su tutt'e due i binari, le chiavi sono state 11, 47, 44, 72, 24, 112, 129 — mai zero.**
⇒ Quel numero **non si riproduce**: era il ramo fortunato della bistabilità, preso una volta e
scambiato per la regola.

**Il binario** — `HEAD` (`2954bf0`) md5 `dae98670…` contro `51b5994` md5 `760c6fd7…`, e fra i due
`src/` cambia in **un commit solo** (+412 righe, 0 tolte):
- ⛔ **sulla linea pulita non conta**: 39,95 contro 39,25 = **1,8 %**, dentro il metro.
  ⇒ `[M]` **il sospetto «la riga `rete-quic` costa» è REFUTATO**: una `registro_dice` in più al
  secondo non si misura;
- conta **solo dove c'è perdita**, e ⭐ **si incrocia**: HEAD rende di più sotto lo 0,5 % (37,0 contro
  29,1 a 0,2 %), meno sopra lo 0,75 %. ⚠ **Ma i rossi sopra lo 0,75 % poggiano su caselle la cui
  dispersione interna (46,6 %) supera il metro**: sono **indizi, non numeri**. Quelli a 0,2/0,3/0,5 %
  sono solidi e dicono tutti la stessa cosa;
- ⭐ e `51b5994` è **già dentro la spirale a ogni casella** (55-142 chiavi): per questo è *stabile* —
  **non ha un bordo su cui oscillare**.

## 17.10 Che cosa resta aperto dopo questa sezione

1. ⭐ **le cure contro la spirale sono MISURATE** (§17.6) e restano **spente**: I6 le tiene dietro
   l'interruttore finché l'utente non le ha guardate. ⇒ ❓ **decisione dell'utente**, e ha i due
   numeri che le servono — il ritmo guadagnato (1,7-2,8 volte) e il ritardo pagato (−38/+161 ms sui
   profili ordinari, 4,5 s su `raffica-forte`);
2. ⛔ **il 36 % di audio rifiutato da ngtcp2** su `casa-cattiva` (§17.2-quater): stessa finestra di
   congestione che nel video produce la spirale, e non è un difetto della cura del riordino;
3. ⭐ **`raffica-forte` è spiegato** (§17.1-quater): non si stacca nessuno, si ferma la consegna —
   `cwnd` a ~10 KB e 860 fotogrammi mai spediti. ⛔ Resta grave (schermo fermo) e **le cure lo
   curano**, ma il nome era sbagliato e il predicato è in cura;
4. ❓ **il fantasma di §17.5**: decisione dell'utente, non di una misura;
5. ⭐ **le cure ai banchi sono applicate e i banchi rifatti girare** (§17.9): nove difetti in tutto,
   ⛔ **tutti della forma «silenzio invece di rosso»**;
5-bis. ⭐ **la contraddizione fra le due griglie è sciolta** (§17.11): non erano due binari, era il
   prodotto che **vicino al bordo è bistabile**. ⛔ E ne è uscito il fatto più importante della
   sezione: **il gradino è doppio** — il meccanismo parte al **primo pacchetto perso**, il sintomo
   si vede **cinque volte più in là**;
5-ter. ⏳ **e la bistabilità non ha una spiegazione**: `[?]` perché lo stesso ingresso dia
   `0 chiavi · 40,16/s` oppure `24 chiavi · 33,84/s` non è stato indagato. È la prima cosa da
   guardare se si vuole curare il difetto **dove comincia** invece che dove si vede;
6. ⚠ **il riordino sugli stream resta senza testimone diretto** (§17.3): `dgram_falsi` vale
   sull'audio soltanto.

---

# §18 · ⭐⭐⭐ LE DUE CURE DECISE DAL REGISTA — *23-24 agosto 2026, notte*

> *«Ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps. Se in 10 secondi non
> arrivano più pacchetti è chiaro che la connessione è morta. […] se all'interno di un intervallo di
> 1-2 secondi c'è una perdita di pacchetti piuttosto copiosa direi di trattarla come il caso in cui
> la connessione è caduta.»*
> — ⇒ `DECISIONI.md` **§3.1-quater**, **§3.1-quinquies**, **§3.1-sexies**.

⛔ **Da dove nasce**: la scelta fra **due mali misurati** (§17.1, §17.6). Con perdita a raffiche
pesanti, **senza** le cure lo schermo si congela **14,26 s**; **con** le cure si muove ma con
**4,5 s di ritardo**. ⇒ L'utente ha deciso che **nessuno dei due va servito**: una linea così non è
lenta, è **rotta**. E alla domanda su che cosa veda, ha scelto fra tre: ✅ **il filo cade e si
rientra a mano** — non un riattacco automatico, non un ripristino invisibile.

⚠ **L'obiezione è stata fatta e superata**: *«su rete cattiva la diagnosi "è caduta la linea" è
frequente, e farla pagare con un accesso a mano rende il prodotto inusabile proprio dove serve»*.
⇒ Da lì nasce il prerequisito: **§18.3, il fantasma**.

## 18.1 ⛔⛔⛔ LA PRIMA GRANDEZZA ERA SBAGLIATA — e il banco l'ha refutata prima che uscisse

La cura fu scritta su `pkt_lost / pkt_sent` di ngtcp2 dentro una finestra: una frazione di perdita,
soglia **50‰ (5,0 %)**, tarata con due margini apparentemente comodi — 2,9× sopra il peggiore che
regge (`casa-cattiva`, 1,71 %) e 2,2× sotto quello che non serve nessuno (`raffica-forte`, 11,10 %).

⛔ **`banchi/09-b81-linea-morta.py` l'ha uccisa in dieci minuti** `[M]`:

| profilo | perdita **iniettata** (sonda) | perdita **DICHIARATA** da ngtcp2 | la linea |
|---|---|---|---|
| `casa-cattiva` | 1,86-2,15 % | ⛔ **512‰** (51,2 %) | **REGGE 10 minuti** — 9,60 fotogrammi/s, copertura 1,00, buco max 0,50 s, cliente attaccato a 599,99 s |
| `raffica-forte` | 12,28-14,00 % | **123‰** (12,3 %) | **non regge** — copertura 0,20, buco 30,06 s |

⛔⛔ **La grandezza ordina i due casi AL CONTRARIO**: la linea che **funziona** dichiara **quattro
volte più perdita** di quella che non funziona. ⇒ **Nessuna soglia le separa** — qualunque valore
lasci passare `casa-cattiva` (≥ 512‰) lascia passare anche `raffica-forte`; qualunque valore fermi
`raffica-forte` (≤ 123‰) ferma **prima** `casa-cattiva`. **Non era una taratura da rifare: era la
grandezza sbagliata.**

⭐⭐ **E la causa è il fatto centrale di questa fase, tornato addosso a noi.** `casa-cattiva` porta
`delay 40ms 20ms distribution normal`, e la sonda ci misura il **93,5 % di pacchetti fuori ordine**
con l'1,9 % di perdita vera. **ngtcp2 conta un pacchetto sorpassato come perso.** ⇒ `pkt_lost` su
una linea che riordina **misura il riordino**, non la perdita — ed è §3.1-ter che ci presenta il
conto: *avevamo scritto che il disordine viene scambiato per perdita, e poi ci abbiamo costruito
sopra una decisione*.

⚠ E non era l'avvio della connessione: tolte le prime dieci finestre, **399 su 399** restano sopra
soglia, mediana **524‰**, ininterrotto per dieci minuti.

⭐ **Il falsificatore era stato dichiarato `[?]` da chi ha scritto la cura**, prima che il banco
girasse: *«la soglia è sulla frazione **dichiarata**, mentre i due estremi sono la perdita
**iniettata** — con jitter e riordino la dichiarata può essere più alta»*. ⇒ È servito: il banco
sapeva **che cosa andare a rompere**, e l'ha rotto al primo giro.

## 18.2 ⭐⭐⭐ LA GRANDEZZA GIUSTA — **lo stallo dell'uscita**

⭐ **I dati la indicavano da soli**: `casa-cattiva` buco massimo **0,50 s**, `raffica-forte`
**30,06 s** — **sessanta volte**. ⇒ Quel che separa i due casi non è **quanto si perde**: è **se i
fotogrammi escono**.

> **la grandezza è: da quanto tempo non esce un fotogramma pur avendone da mandare**

Due contatori **locali e monotoni** (forma P8→P20 di `RCP.md`: un fatto osservabile, mai un
orologio) più un istante:

| | come si calcola |
|---|---|
| **«è uscito»** | i **byte di video consegnati a ngtcp2** in `coda_consegna()` — l'unico punto in cui i byte sono davvero dentro un pacchetto |
| **«avevo da mandare»** | coda video non vuota **oppure** `lm_offerti` salito (in `video_a_una()`, **prima** di freno, sgombero e rifiuto) |

⛔⭐ **Il secondo termine non è un di più, ed è la riga che rende la cura onesta**: senza
`lm_offerti`, **il regolatore del ritmo nasconderebbe lo stallo** — smette di produrre,
`video_sgombra()` abbandona i delta, la coda si svuota, e *«non ho niente da mandare»* diventa vero
**mentre lo schermo è fermo**. La cura si assolverebbe da sola proprio nel caso che deve prendere.

⛔ **E se non c'è niente da mandare il conto non parte nemmeno**: `[M]` in questa fase la scena ferma
consegna **1 fotogramma in 30 s e poi zero** — e non è un difetto, è `RecordVirtual` di Mutter che
consegna solo sul cambiamento (§13, il risveglio costa 13 ms). ⇒ Una cura che partisse lì
**butterebbe fuori chi guarda un desktop fermo**, che è il modo peggiore in cui potrebbe fallire.

⚠ **Si contano i byte, non i fotogrammi interi**, e la ragione è dichiarata: una chiave da ~60 000
byte su linea stretta può metterci secondi a uscire tutta, e a fotogrammi quei secondi sarebbero uno
«stallo» **mentre il filo lavora**. Un byte che parte è un filo che porta.

### 18.2-bis La soglia — **5 000 ms**, e i due margini col caso intermedio

| | stallo/buco più lungo | |
|---|---|---|
| tredici profili sani | 0,04-0,35 s | reggono |
| `casa-cattiva` | **0,50 s** | ⛔ **REGGE — non va dichiarata morta** |
| ⚠ `raffica-1` | **un secondo intero a zero** | ma consegna **23,94 fotogrammi/s**: regge benissimo |
| `raffica-forte` | **14,26 s** (30,06 nell'altro giro) | non regge |

⇒ intervallo **1,00-14,26 s**, centro geometrico **3,78 s**, scelta **5,0 s** — ⭐ **sopra** il
centro, apposta. Margine **5,0×** sopra il peggiore che regge, **2,9×** sotto quello che non serve.

⛔ **Il lato stretto usa il PIÙ CORTO dei due stalli di `raffica-forte`**, non il più lungo: un
margine scritto sul numero fortunato non è un margine.
⛔ **E l'asimmetria è voluta**: i due errori **non costano uguale**. Sbagliare in alto = qualche
secondo di schermo fermo in più. Sbagliare in basso = **buttare fuori uno che stava lavorando**, e
non si rimedia.
⚠ **Anche il campionamento sbaglia dalla parte buona**: il conto riparte dall'istante del giro
(≤ 1/s), non da quando i byte sono usciti davvero ⇒ lo `stallo_ms` misurato può essere fino a ~1 s
**più corto** del vero. Si scatta più tardi, mai più presto.

### 18.2-ter ⭐⭐ LA PROVA — *24 agosto 2026*, e il margine è **misurato**, non «non è scattato»

⛔ La riga esce **solo allo scatto**. ⇒ Un «non è scattato» non dice **quanto ci è mancato**: il
banco ribatte lo stesso profilo **con soglie sempre più basse** finché una scatta, e allora il
prodotto stampa il suo `stallo_ms`.

| profilo | stallo massimo | margine sulla soglia di 5 000 ms | buco al client |
|---|---|---|---|
| `ritardo-30` (sano) | < 500 ms | **> 10×** | 0,157-0,175 s |
| ⭐ `casa-cattiva` | < 500 ms | **> 10×** | 0,359-0,479 s |
| ⚠ `raffica-1` | **1 001 ms** | **5,0×** | 0,52-3,73 s |
| ⛔ scena **ferma** | *il conto non parte* | — | 1 e 3 fotogrammi in 90 s |

⭐ **`raffica-1` conferma la derivazione con un numero indipendente**: il lato stretto vale
**1,00 s**, esattamente quello del riquadro, e il margine sono i **5,0×** dichiarati.

**`casa-cattiva`, dieci minuti, cura accesa: ZERO SCATTI** — 9,71 fotogrammi/s, copertura **1,00**
(600 s su 600), buco massimo **0,479 s**, cliente attaccato a 599,88 s, nessun congedo.

⭐⭐ **E il confronto che chiude la refuta**, nello **stesso** giro: il **testimone** dice `permille`
mediana **529‰**, con **392 finestre su 392** sopra i vecchi 50‰. ⇒ **La cura vecchia avrebbe ucciso
questa identica sessione; la nuova non la tocca.** Stesso profilo, stesso banco, stessi dieci
minuti: cambia **solo la grandezza su cui si decide**. E dall'altro lato `raffica-forte` — quella
che *non* regge — dichiara `permille=133`, cioè **meno**.

**Lo scatto vero** `[M]`: `raffica-forte` (13,19 % iniettato) scatta a **18,95 s**, con
`causa=stallo stallo_ms=5008 · offerti=198 · usciti_byte=0 · coda_video=31146` — ⭐ **le due metà
tutt'e due vere**: avevamo da mandare, e non è uscito niente. E il filo cade.

**Il silenzio** `[M]`: `kill -9` ⇒ `silenzio_ms=10006`, `prove=12`, **10,24 s** dopo il colpo, e
nella stessa riga `stallo_ms=8 offerti=0` — ⭐ **le due cause restano separate**. A cura spenta,
zero scatti.

**La scena ferma** `[M]`: 90 s di desktop che non cambia, zero scatti alla soglia in vigore **e a
1 000 ms**, cioè cinque volte più stretta. ⭐ E la scena era ferma **davvero, verificato e non
sperato**: il conto del server dice 1 e 3 fotogrammi in 90 s, tutti spediti.

**I predefiniti (I6)** `[M]`: senza `--linea-morta`, zero scatti e zero sfratti, e i due profili
stanno nella griglia di §17.

⚠ **Una cosa da dire, e va nel verso prudente**: lo **stallo** (server: byte usciti) e il **buco**
(client: fotogrammi arrivati) **non sono la stessa grandezza**, e la soglia è derivata dal secondo
mentre la cura misura il primo. `[M]` su `raffica-1` un giro ha dato buco **3,73 s** con lo stallo
che non scattava nemmeno a 1 000 ms: **i byte partono, a mancare è la ritrasmissione**. ⇒ L'errore
va dalla parte buona, ma il numero della derivazione è **prudente, non esatto**.

### 18.2-quater ⛔ Che fine ha fatto il `permille` — da **giudice** a **testimone**

`--linea-morta-permille` è **tolta**: un'opzione che accetta un numero **senza usarlo** è peggio di
un'opzione che non c'è, perché chi la batte crede di aver tarato qualcosa. ⇒ Adesso si becca aiuto e
uscita 2.
⭐ Ma `permille=` **resta nella riga come testimone**: è la miglior misura di **riordino** che il
server abbia **sugli stream**, dove `dgram_falsi` (§17.3) non arriva. ⚠ E il banco verifica
l'**assenza** dell'opzione **battendola**, non con un `grep`: `[M]` la stringa nel binario c'è
eccome — sta nel testo d'aiuto — e il primo giro di quel controllo **ha dato rosso su un binario
giusto**.

## 18.3 ⭐⭐ LO SFRATTO DEL FANTASMA — e abbassare `SILENZIO` è stato scartato **su una misura**

⛔ La strada ovvia — portare `SILENZIO` da 30 s a 10 — **si rompe**, `[M]` 16 agosto: fra due
pacchetti autenticati di un **browser fermo ma VIVO** passano **15 004 / 15 005 / 15 002 ms**. È il
keep-alive del browser, non nostro. ⇒ A 10 s **ogni client che guarda e non tocca perde il posto a
ogni giro di keep-alive** — è la regressione già pagata il 16 agosto (*«una seconda scheda è entrata
e ha preso il desktop del primo»*).

⚠ **E `SILENZIO` ne governa altri quattro**: l'avviso a `SILENZIO/2` (passerebbe da «mai su una
sessione sana» a «su tutte»), il rilascio dei tasti premuti (⛔ un `Ctrl` tenuto giù durante una
pausa di rete di 12 s verrebbe rilasciato **sotto le dita**), l'ordine silenzio→inattività, e **tre
documenti** che dichiarano il numero all'utente.

⇒ **La strada scelta è più stretta e più mirata**: `--sfratto-ms N` (**0 = spento**, predefinito;
consigliato **15 000**). Scatta **solo quando qualcuno chiede quel posto**, mai da solo, e **solo fra
client dello stesso utente**.

⛔ **§8.2 non è violata, è applicata**: *«nessun client attaccato e **vivo** viene mai spodestato»* —
l'occupante qui è attaccato ma **non vivo**, e finora l'unico orologio che li distinguesse era quello
da 30 s. ⭐ `torna_a_parlare()` riparte **solo da `S_STACCATA`**: per questo lo sfratto cambia lo
**stato** e non si limita a togliere il posto, o il fantasma resterebbe `S_ATTIVA` senza posto.

`[M]` **Il fantasma scende del 48 %**: da **32,13 s e 14 rifiuti** a **16,83 s e 7 rifiuti**. ⭐ E con
la linea morta accesa scende a **~10 s con zero rifiuti** — il posto torna libero al primo tentativo.

**Due utenti diversi** `[M]`: zero sfratti, il secondo utente entra sul **proprio** posto con zero
rifiuti. ⚠ La riga `⛔ SFRATTO NEGATO` **non esce**, ed era previsto `[R]` prima di girare: il
registro dei posti è indicizzato per nome, quindi `POSTO_OCCUPATO` implica già «stesso utente» e quel
ramo non è raggiungibile. **La protezione la fa la struttura; il controllo esplicito resta come
rete** — il giorno in cui `MAX_ATTACCATE` diventa la tabella di un server multi-tenant sarebbe
l'unica cosa a reggere.

## 18.4 ⛔ E LA FRASE CHE MENTIVA

*«Quell'utente è già collegato da un altro dispositivo»* (`src/pagina.html`, `MOTIVO[0x0F]`) è una
**diagnosi che il server non è in grado di fare**: non sa se l'altro client è un altro apparecchio o
è lo stesso utente appena caduto. ⇒ Adesso dice **quel che sa** e dà il gesto:

> *«il posto di questa sessione risulta occupato da un altro client — se eri tu e sei appena caduto,
> riprova fra qualche secondo»*

⚠ **E conta più di prima**: dopo §3.1-quater **si rientra a mano**, quindi è la **prima frase che
l'utente incontra rientrando**.

## 18.5 ⚠ E un prezzo dichiarato per un caso che non esiste — corretto

I PING passano a metà della soglia quando la cura è accesa, e il costo era stato dichiarato in
**0,21 kbit/s** per sessione. ⛔ Il banco **non ha potuto isolarlo, e si è rifiutato di dare un verde
vuoto**: `[M]` una sessione «ferma» costa comunque **2 463 kbit/s** di audio PCM (§4.3, che non si
spegne — un `CIAO` senza codec audio comune si becca `0x09 NIENTE_IN_COMUNE`), cioè **11 727 volte**
quel numero; la differenza acceso−spento è **+0,539 kbit/s**, dentro il rumore.

⭐ **E il fatto vero**: `[M]` su una sessione viva il contatore **non si ferma mai per 0,6 s** ⇒ il
keep-alive **non ha mai occasione di scattare**, e quei 0,21 kbit/s descrivevano **un caso in cui il
prodotto non entra**. Un prezzo dichiarato per un caso che non esiste **è peggio di nessun prezzo**.

## 18.6 Che cosa resta, dopo §18

1. ⭐ **le due cure sono provate e restano SPENTE** (I6): `--linea-morta` e `--sfratto-ms`.
   ❓ **La decisione di accenderle è dell'utente**, e ora ha i numeri;
2. ⏳ **le cure contro la spirale** (§17.6) restano spente e aspettano **i suoi occhi**, che è l'unica
   cosa che non si può delegare a una misura;
3. ⏳ **la bistabilità** di §17.11 non ha ancora una spiegazione;
4. ⛔ **il 36 % di audio rifiutato da ngtcp2** su `casa-cattiva` (§17.2-quater) non ha ancora una cura;
5. ⚠ **lo stallo e il buco non sono la stessa grandezza** (§18.2-ter): la derivazione è prudente, non
   esatta, e un giro che le misuri **insieme** la renderebbe esatta.

---

# §19 · ⭐⭐⭐ IL GIUDIZIO DELL'UTENTE SUL PERCORSO VERO — *24 agosto 2026, mattina*

⛔ **È la sezione che conta più di tutte le altre**, e per la ragione scritta in testa al documento: in
v1 la fase omologa fu validata con PSNR, SSIM e l'occhio dello sviluppatore, e il giudizio
dell'utente sul desktop vero fu *«siamo tornati indietro»*. **La fase fu azzerata.**

**Il banco**: sessione vera dell'utente, browser sul **portatile** (192.168.0.3, WiFi `wlo1`), server
sulla macchina di prova, porta **7920**, binario `2792271f…` dall'albero di lavoro, tela
**2544×926**, ⛔ **tutte le cure spente**, trappola di glibc **spenta** (il server gira alla velocità
vera).

⭐ **E la rete si è sporcata dal lato del CLIENTE**, non del server: il video arriva in **ingresso**
su `wlo1`, quindi il guasto sta su un `ifb0` con `netem`, alimentato da un filtro `u32` sulla **sola
porta UDP 7920 in arrivo**. ⛔ Sulla macchina di prova lo stesso traffico passerebbe da `enp7s0`,
dove passa l'ssh, e quella non si tocca. L'ssh è TCP sulla 22 e non è filtrato.
⚠ E il guasto **si disarma da sé** dopo N secondi, con un guardiano staccato: la stessa disciplina
già usata su `lo`.

## 19.1 ⭐⭐⭐ LA SCALA, E VIENE DAI SUOI OCCHI

| perdita **misurata sul filo** | il suo giudizio |
|---|---|
| 1 % | *«mi sembra ok»* |
| **5,6 %** | *«è tutto fluido»* |
| ⛔ **10 %** | *«adesso si è bloccato»* |

> ⇒ **Il confine dell'uso reale sta fra il 5 e il 10 per cento di perdita.**

⛔⛔ **E questo CONTRADDICE il banco, di un ordine di grandezza.** §17.11 mette il dirupo dentro il
primo punto percentuale: la spirale di chiavi parte allo **0,10 %** e il ritmo casca sotto il
pavimento allo **0,53-0,75 %**. `[M]` Sul percorso vero, al **5,6 %** — cioè da **sette a
cinquantasei volte** più perdita — l'utente non se ne accorge.

## 19.2 ⛔ E LA PROVA È STATA RIFATTA DUE VOLTE, PERCHÉ LA PRIMA NON MORDEVA

⚠ **Va scritto perché è un errore di metodo mio, ed è il terzo della stessa famiglia** (dopo il
video pieno di grana di §16.4 e i nove «attesi» mai confrontati di R13): un giudizio su una prova che
non sollecita non è un giudizio.

`[M]` **Primo giro, e non valeva**: perdita all'1 % accesa e verificata (il server la vedeva:
*«la linea perde»*, 27 pacchetti dichiarati persi, 22 datagram audio perduti), **zero fotogrammi
abbandonati su 920**, **due chiavi in tutto**. ⇒ Nessuna spirale — ma la ragione era nel numero che
non stavo guardando: ⛔ **i suoi fotogrammi pesavano 242-283 byte.** Duecento byte. Il banco crollava
su una scena che riempiva il filo con 3 Mbit/s; qui la perdita **non aveva niente da rompere**.

`[M]` **Secondo tentativo, il trascinamento di una finestra**: fotogrammi fino a **3 801 byte**,
**zero chiavi** su 400, **2 abbandoni su 2 181**. ⇒ Ancora insufficiente: il banco lavorava su
fotogrammi **sette volte più grossi**.

`[M]` **E al 5 % il primo giudizio è stato RITIRATO prima di scriverlo**, contando i pacchetti
passati davvero dentro il guasto: **221, con 18 buttati**. ⛔ Diciotto pacchetti non sono una prova.
⇒ Rifatto con **trenta secondi senza mai fermarsi**, e allora sì: **7 596 pacchetti nel guasto, 423
buttati = 5,6 % reale**.

⭐ **Il numero che rende valido il giro buono** — e che mancava ai due precedenti: fotogrammi fino a
**77 304 byte**, cioè ⭐ **tre volte più grossi di quelli su cui il banco crollava**. Con quelli:
**chiavi 3,8 %** (23 su 600), **abbandoni 11 su 3 017** (0,36 %), e il giudizio *«è tutto fluido»*.

⛔ **La lezione, e vale oltre questa fase**: il gradino non lo decide la perdita, lo decide **quanto
la scena chiede**. Il banco produce una sollecitazione che pretende **quaranta fotogrammi al secondo
di cambiamento continuo**; un desktop vero — anche mentre si trascina una finestra — cambia **a
strappi**. ⇒ **Non è la stessa sollecitazione**, e le previsioni del banco **non si applicano al
prodotto così com'è usato**.

## 19.3 ⭐⭐ IL BLOCCO AL 10 %, COLTO NELL'ISTANTE — e il meccanismo è quello di §17.1-ter

`[M]` Nel momento in cui l'utente ha detto *«si è bloccato»*, il registro del server diceva:

| | |
|---|---|
| **`cwnd = 2 888 byte`** | ⛔ la finestra di congestione **collassata a due pacchetti** — dieci volte meno del minuto prima |
| `cwnd_left = 2 888` · **in volo = 0** | ⛔⭐ **non è che il filo sia pieno: non c'è NIENTE in volo.** Il server *potrebbe* mandare, e non manda |
| **27 fotogrammi `NON SPEDITO`** | e il contatore dei consegnati **fermo a 3 117** su tre letture di fila |
| chiavi | salite da 4 a **16** |
| `persi=664` · `dgram_persi=493` | `giudizio=⛔ la linea perde` |

⇒ ⭐ **È esattamente la catena di §17.1-ter, vista sul percorso vero**: la finestra si chiude → i
fotogrammi non partono → si chiedono chiavi → lo schermo si ferma. Il meccanismo del banco **è
giusto**; sbagliato era **dove** lo collocava.

⭐⭐ **E `cwnd_left = cwnd` con «in volo = 0» è la firma che assolve il filo e accusa noi**: non è
congestione osservata, è il pacer che rifiuta. È lo stesso quadro di `raffica-forte` (§17.9-quater,
`cwnd` mediana 8 948 B, `cwnd_left` mediana 0) su una linea vera.

## 19.4 ⚠ E DUE COSE CHE QUESTA SESSIONE NON HA POTUTO PROVARE

1. ⛔⛔ ~~**Le applicazioni che il coordinatore avvia non arrivano sullo schermo dell'utente.**~~
   → **ERRATA, e la correzione è in §20.1.** `[M]` `mpv` **arriva eccome** — 241 fotogrammi in 8 s
   su un banco controllato. Quando l'ho giudicato *«non arriva»* ⛔ **non c'era nessun cliente
   attaccato**: il server non spediva, e il contatore era fermo **per costruzione**. I «167 byte»
   erano gli ultimi valori di prima.
   ⚠ **Ho giudicato con un metro che in quella scena non poteva dire niente**, ed è la stessa ferita
   di §19.2 — la terza volta in due giorni. **Firefox** invece è rotto davvero, ma `[M]` **anche
   fuori da REMOTIX**: non è nostro (§20.1).
2. ⭐ **Le cure sono state provate a occhio** ⇒ **§19.6**, e il verdetto è che **fanno quel che
   promettevano e non basta**.

## 19.6 ⭐⭐⭐ LE CURE, GUARDATE — **fanno quel che promettevano, e non basta**

`[M]` 24 agosto, stessa sessione, stesso binario, **stesso 10 % di perdita**, e a cambiare **solo
gli interruttori del server** — verificati dalle righe d'avvio, non dalla riga di comando: soglia
della coda **100 ms**, regolatore del ritmo **ACCESO**, ⛔ **linea morta e sfratto SPENTI di
proposito** (se il filo cadesse non si saprebbe se è merito o colpa delle cure).

Perdita **misurata sul filo**: 8 597 pacchetti passati, **905 buttati = 10,5 %**.

| | **senza** cure | **con** le cure |
|---|---|---|
| fotogrammi consegnati | ⛔ **fermi** — stesso numero su tre letture di fila | ⭐ **continuano**: 1533 → 1552 → 1557 |
| fotogrammi mai spediti | **27**, in una raffica | ⭐ **1** |
| `cwnd` | 2 888 B | 3 652 B |
| chiavi | 16 | 17 |
| **il giudizio dell'utente** | *«si è bloccato»* | ⛔ *«si è bloccato»* |

⭐ **Le cure fanno esattamente quel che il banco prometteva**: senza, la consegna si **ferma**; con,
va avanti a **cinque-venti fotogrammi al secondo**, e i fotogrammi mai spediti passano da 27 a **1**.
Il meccanismo è curato.

⛔⛔ **E non basta.** Per chi guarda, cinque fotogrammi al secondo con quel ritardo **sono un blocco
lo stesso**. ⇒ Il numero migliora e **l'esperienza no**, ed è precisamente la distinzione che questa
fase esisteva per proteggere (v1: *«siamo tornati indietro»* su numeri che erano migliorati).

⭐⭐⭐ **E questo è l'argomento più forte a favore di §3.1-quater**, la decisione presa dall'utente
la notte prima **senza avere questo numero**: al 10 % di perdita **non esiste una versione buona** —
o lo schermo si ferma, o si muove in un modo che l'utente chiama **comunque bloccato**. ⇒ *«Nessuno
dei due va servito»* non era una preferenza: era la lettura giusta, e adesso ha la prova.

**La scala completa, tutta dai suoi occhi:**

| perdita reale | **senza** cure | **con** cure |
|---|---|---|
| 1 % | *«mi sembra ok»* | — |
| 5,6 % | *«è tutto fluido»* | — |
| **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |

### 19.6-bis ⚠ E DUE COSE VISTE DI PASSAGGIO, che non erano nel programma

1. ⭐ **La regola dei sessanta minuti ha scattato su una sessione vera, ed è la prima volta.**
   `[M]` *«prova2 non tocca niente da 3 600 012 ms (tetto 3 600 000) — CHIUDO la sessione grafica»*
   (`DECISIONI.md` §4.8). Ha chiesto l'uscita gentilmente e, **dopo dieci secondi**, l'ha chiusa a
   forza (`Logout 1` → `Logout 2`). ⚠ E ha prodotto un falso allarme: l'utente ha visto lo schermo
   fermo e ha detto *«il server è ancora bloccato»* — ⛔ **non lo era**: `NRestarts=0`, acceso da
   un'ora e mezza, e il solo core presente era di **ieri**.
2. ⛔⭐ **«Sessione viva e muta» è indistinguibile da «programma morto», e l'utente l'ha dimostrato
   di persona** — due volte, dicendo *«si è bloccato»* e *«il server è ancora bloccato»* di un
   server che stava benissimo. ⇒ È lo stesso fatto di §17.1-quater e §17.9-quater visto **dall'altro
   lato**: là il banco chiamava «stacco» una consegna ferma, qui l'utente chiama «server bloccato»
   la stessa cosa. ⭐ **Ed è la ragione per cui la cura della linea morta serve**: non perché
   migliori l'immagine — non può — ma perché **dice la verità** invece di lasciare uno schermo fermo
   che sembra un guasto del programma.
   ⚠ E la sessione **si riprende da sé**: `[M]` tolta la perdita, `cwnd` risale da 2 888 a
   **46 412 byte** (sedici volte) senza che nessuno tocchi niente.

## 19.5 ⭐ Che cosa questa sezione cambia nelle decisioni

1. ⭐⭐ **Le cure servono, ma non per il lavoro quotidiano dell'utente.** `[M]` Fino al 5,6 % di
   perdita il prodotto **così com'è** è giudicato fluido. ⇒ Le cure servono al **caso a raffiche** e a
   **chi guarda video**, non a chi lavora. ⚠ È un buon motivo per accenderle **con calma**, e non di
   corsa — e I6 resta rispettata senza costi;
1-bis. ⛔ **E al 10 % non salvano l'esperienza** (§19.6): curano il meccanismo — consegna che continua
   invece di fermarsi, fotogrammi mai spediti da 27 a 1 — ma il giudizio dell'utente **non cambia**.
   ⇒ Sopra una certa perdita **la scala di degradazione non ha più niente da offrire**, e l'unica
   risposta onesta è §3.1-quater: dichiarare la linea morta;
2. ⛔ **Il pavimento di banda (§3.1-sexies, 30 Mbit/s) non c'entra niente con tutto questo.** `[M]`
   Nel giro buono i fotogrammi grossi arrivavano a 77 KB e la linea non era mai satura: quel che si
   chiudeva era la **finestra di congestione**, non la banda. ⇒ ⭐ **§3.1-ter riceve la sua conferma
   più forte**: la banda è una premessa, la grandezza che decide è la **qualità** del filo;
3. ⚠ **e le soglie del banco vanno lette per quel che sono**: `[M]` misure su una sollecitazione
   **dieci volte più severa** dell'uso reale. Non sono sbagliate — sono un **caso peggiore**, e va
   scritto accanto a ogni numero di §17 che qualcuno potrebbe prendere per una promessa.

---

# §20 · ⭐⭐⭐ I PUNTI APERTI, CHIUSI — *24 agosto 2026*

⛔ **E due dei quattro hanno demolito una premessa che questo documento dava per buona.** Si scrive
la correzione, non si liscia.

## 20.1 ⛔⛔ «LE APPLICAZIONI NON ARRIVANO SULLO SCHERMO» — **era falso, ed era mio**

`banchi/09-b82-mostra.sh` · binario `b86cf6df…` dall'albero di lavoro.

⭐ **`mpv` arriva eccome.** `[M]` Con **solo** `XDG_RUNTIME_DIR` + `WAYLAND_DISPLAY`: **241
fotogrammi in 8 s, 38 513 byte medi**. Con `systemd-run --user` (la strada del menu): **317**. E
`WAYLAND_DISPLAY` **c'era già** nell'ambiente del gestore d'utente — ce lo scrive GNOME.

⇒ ⛔ **La causa vera del caso di stamattina: non c'era nessuno che guardava.** `[M]` Il registro
della 7920, minuto per minuto:

```
08:33   765 fotogrammi ·  49 battiti rete-quic
08:34   708 fotogrammi ·  59 battiti
08:35   228 fotogrammi ·  60 battiti
08:36    13 fotogrammi ·  31 battiti   ← il cliente se ne va
poi     NIENTE, solo «il legame regge» ogni minuto
```

Senza un cliente attaccato il server **non spedisce**, il contatore è fermo **per costruzione**, e i
«167 byte» erano gli ultimi valori di prima. ⚠ **Ho giudicato in una scena in cui il metro non
poteva dire niente** — la terza volta in due giorni (§19.2, §16.4).

**Le tre ipotesi che avevo scritto sono tutte cadute** `[M]`: un solo compositore e un solo
`wayland-0` (⚠ la data del 23 agosto che avevo letto era quella di `bus`, non del socket); **un
monitor solo**, `Meta-0` «Virtual remote monitor» 2544×926 scala 1,000; l'ambiente **non** era
incompleto.

### 20.1-bis ⛔ E ANCHE IL METRO ERA SBAGLIATO — i byte non dicono quel che credevo

`[M]` Calibrazione su finestre di 8 s:

| scena | fotogrammi | byte medi |
|---|---|---|
| desktop fermo | 0-1 | 238-283 |
| ⛔ una **bandiera a schermo intero** | **321** | **268** |
| `film-grana.webm` | 226 | 18 600 |
| `duro.mp4` | 240 | 37 081 |

⇒ **Una finestra viva a schermo intero può produrre fotogrammi da 268 byte, cioè quanto un desktop
fermo.** ⭐ **Il verdetto è il CONTO, non i byte**: i byte dicono *quanto* cambia, il conto dice *se*
cambia. ⚠ E in §19.2 avevo usato i byte come metro: quel ragionamento regge sul merito (i suoi
fotogrammi *erano* piccoli) ma il metro giusto era un altro.

### 20.1-ter ⛔⛔⛔ ~~Firefox è rotto — e non è nostro~~ → **REFUTATA il 25 agosto 2026**

> ## ⛔⛔⛔ QUESTA SEZIONE È SBAGLIATA, E LA PROVA CHE LA CHIUDEVA ERA VIZIATA
>
> *Refutata nella fase 10, `fasi/10-multi-tenant-e-il-budget.md` §5.10.* ⭐ **Firefox non è mai stato
> rotto su questa macchina.**
>
> ⛔ **La causa vera**: `~/.cache` è un **collegamento a `/tmp`** (da `/etc/skel`, immagine base del
> 30 luglio). Firefox tiene il profilo *locale* sotto `$HOME/.cache/mozilla` = **`/tmp/mozilla`**, e
> `[M]` **`/tmp/mozilla` appartiene a `prova2`, modo `0700`, creata il 23 agosto alle 08:03** — cioè
> **prima** di tutte le misure di questa sezione. ⇒ Per ogni altro utente il profilo **non nasce**.
>
> ### ⛔⛔ E il difetto di METODO è nel «controllo che chiude la questione»
>
> Diceva: *«`firefox --headless --screenshot` come **`nicfio`** — nessuna sessione REMOTIX, nessun
> Wayland, nessun monitor — **si pianta uguale**»*.
>
> ⇒ ⛔ **Ma `nicfio` ha lo STESSO `~/.cache -> /tmp`**, e quindi lo stesso `/tmp/mozilla` di
> `prova2`. `[M]` Verificato il 25 agosto: `lrwxrwxrwx nicfio -> /tmp`, e dentro
> `drwx------ prova2 prova2`.
>
> ⭐⭐ **Il controllo CONDIVIDEVA il fattore che avrebbe dovuto escludere** — e un controllo così non
> controlla niente: mostra lo stesso guasto per la stessa ragione, e chi lo legge conclude *«allora
> non è la sessione»* quando invece **non era mai stata in prova la sessione**.
>
> ### ⭐ La rimisura, con la sola cosa cambiata
>
> `~/.cache` di `nicfio` rifatta **cartella vera**, e **niente altro** — stesso comando, stessa
> macchina, stesso Firefox:
>
> | | fase 9, 24 agosto | ⭐ 25 agosto, dopo |
> |---|---|---|
> | `firefox --headless --screenshot` come `nicfio` | ⛔ **si pianta**, ucciso a **60 s**, profilo vuoto | ⭐ **`rc=0`**, e uno scatto da **5,5 MB** |
>
> ⚠ **Restano veri i due indizi in fondo alla sezione** (*«More than 1 GPU vendor detected»*, la
> Radeon recintata): ⛔ **sono avvertimenti, non la causa** — la stessa riga esce anche adesso, col
> browser che funziona.
>
> ⭐ **E quel che resta di giusto**: *«il difetto c'è, la diagnosi no»*, scritto qui in fondo il 24
> agosto. ⇒ **Era la frase esatta**, ed è quella che andava seguita invece di chiudere con un ✅.

### ~~20.1-ter~~ *(il testo originale, conservato)* ✅ Firefox è rotto — **e non è nostro**

`[M]` Firefox `140.14.0esr`: vivo (80 thread, 126 MB), **zero fotogrammi dopo 90 s**, mai attaccato
al socket Wayland. Fallisce identico da `systemd-run --user`, con `--profile` esplicito, con
`MOZ_CRASHREPORTER_DISABLE`, `MOZ_DISABLE_GPU_PROCESS`, `LIBGL_ALWAYS_SOFTWARE`,
`MOZ_ENABLE_WAYLAND=0`, sandbox spente.

⭐⭐ **Il controllo che chiude la questione**: `firefox --headless --screenshot` come **`nicfio`** —
nessuna sessione REMOTIX, nessun Wayland, nessun monitor — **si pianta uguale** e viene ucciso a
60 s col profilo vuoto. ⇒ **Firefox è rotto su questa macchina per tutti, dentro e fuori REMOTIX.**
Non è un difetto del prodotto, e §14.7/§16.5 vanno lette così.

⚠ Due indizi per chi lo riprenderà: `[GFX1-]: More than 1 GPU vendor detected via PCI, cannot deduce
vendor` (Intel `0x8086/0x4680` + AMD `0x1002/0x73bf`), e `/dev/dri/renderD129` è del gruppo
`remotix-nogpu` — la scheda AMD è recintata **apposta** (§4.6-ter).
⭐ E il `[M]` del 23 agosto (*«il profilo non viene mai creato in `~/.mozilla/firefox/`»*) guardava
**il posto sbagliato**: Debian `firefox-esr` usa `~/.mozilla/firefox-esr/`. ⚠ Anche quella resta
vuota — il difetto c'è, la diagnosi no.

### 20.1-quater ⭐ Lo strumento che mancava — `banchi/09-b82-mostra.sh`

Lancia un comando dentro la sessione di un utente con `systemd-run --user` (cioè in `app.slice`,
dove finirebbe scegliendolo dal menu), poi **conta i fotogrammi prima e dopo e dà il verdetto su quel
numero** — ⛔ mai su *«il processo è vivo»*. Quattro guardie: un compositore solo · un monitor solo e
nostro · l'ambiente **letto** da `systemctl --user show-environment` invece che inventato · e
⭐⭐ **G4: c'è qualcuno che guarda?** — zero battiti `rete-quic` ⇒ **nessun verdetto**.

⭐ **G4 è nata da un rosso su codice giusto**, ed è la guardia che avrebbe evitato le tre prove
bloccate di stamattina. Provata nei tre versi: `mpv` 240 contro 0 (verde) · `gnome-terminal` 40
contro 1 (verde) · `firefox` 0 contro 1 (rosso) · senza cliente, **si rifiuta di giudicare**.

⛔ **E non c'era niente da curare in `src/`**: il figlio prepara la sessione bene — un compositore, un
monitor, scala 1,0, ambiente completo. La cura era **nel modo di giudicare**.

## 20.2 ⛔⛔⛔ L'AUDIO — la premessa era falsa, e sotto c'era di peggio

### 20.2-bis ⛔ «Il 36 % dell'audio non raggiunge il filo» era una proprietà **del banco**

`[M]` Il registro della 7920, **quattro attacchi su quattro** della sessione vera dell'utente:
`negoziato … audio.codec=opus` → `canale audio ACCESO — codec 1 (Opus)`.

⇒ ⛔ **L'utente non è mai stato su PCM.** `[R]` Il PCM lo impongono **i banchi**: `09-b68:191`,
`09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294` passano tutti `--audio-codec pcm`.
⇒ **§17.2-quater e §18.5 vanno lette così**: il 36 % di rifiutati e i 2 463 kbit/s sono proprietà di
una **configurazione di banco**, non del prodotto in uso.

### 20.2-ter ⭐⭐⭐ E QUEL CHE C'ERA SOTTO: **si spendono 589 kbit/s per portare 1,2 kbit/s di silenzio**

`[M]` Che cosa viene rifiutato, sulla sessione **vera**: `datagram di 16 byte` = 1 (prefisso) + 12
(§6.3) + **3 di carico**. Riprodotto sul banco: `codec 1 (Opus), 3 byte di carico`, 1 248 su 1 248, e
`suono.c` dice **`PICCO 0 su 32767`**. ⇒ **Si rifiuta il silenzio digitale.**

`[M]` A desktop fermo, Opus: **48,0 datagram al secondo su 48,4 pacchetti** — il filo è *tutto*
audio — e ogni pacchetto è **pieno**, 1 441 byte su 1 452, per il `PADDING`.

**La cura** (`src/audio.c`, ⛔ nasce **spenta**, I6): un blocco in cui **tutti** i campioni sono
esattamente zero **non diventa un datagram**. ⭐ La ragione per cui è lecito: §6.3 mette l'`istante`
in ogni blocco e chi riceve lo rimette al posto assoluto ⇒ **un blocco non spedito è un buco, e un
buco è silenzio** — che è esattamente quel che quel blocco conteneva. ⛔ Nessuna soglia: **solo lo
zero digitale**, l'unico caso in cui «spedito» e «non spedito» suonano identici.

| desktop fermo, Opus | sul filo | pacchetti/s | datagram/s | byte/pacchetto | carico utile |
|---|---|---|---|---|---|
| **spenta** | 557,6 kbit/s | 48,4 | 48,0 | 1 441 | 1,18 kbit/s |
| ⭐ **accesa** | **5,5 kbit/s** | 0,5 | 0,0 | — | 0,00 |

⇒ ⭐⭐ **102,1 volte**, e 1 248 blocchi taciuti su 1 248. **Oggi una sessione ferma spende 589 kbit/s
per portare 1,2 kbit/s di silenzio: il 99,8 % è riempimento.**

**Il controllo che protegge l'utente** (tono a 440 Hz nel sink, giudice di `07-b42`): copertura
**1,0000 → 0,9996**, purezza del tono **1,000 → 1,000**, blocchi taciuti **1 su 5 001** — e quell'uno
precede i primi campioni. ⚠ Prezzo dichiarato: i `mancati` del cliente vanno da 0 a 2 (un buco voluto
lascia lo stesso salto di `istante` di uno perso).

⚠ ~~L'interruttore oggi è **di compilazione** (`-DAUDIO_SILENZIO_PREDEFINITO=1`) … ⏳ la riga di
comando è **descritta e non scritta**.~~
> ✅ **SCRITTA, il 24 agosto 2026** *(riallineato al codice il 28)*. Il `-D` **è stato tolto**, e
> l'unica strada è **`--niente-audio-silenzio`** sulla riga di comando del server, che `figlio.c`
> ricopia in coda all'`argv` del figlio come fa già con `--parlantina`. ⛔ E vale per **due
> processi**: il codificatore vero sta nel figlio, ma il tono di `--audio-prova` apre un `audio_cod`
> nel server — se se ne accendesse uno solo, i due banchi misurerebbero due prodotti diversi.
> ⚠ La ragione per cui non ce ne sono due: *«due strade per la stessa cura sono due numeri che
> divergono»* (`src/audio.h`).

### 20.2-quater ⛔ DUE DIFETTI TROVATI STRADA FACENDO, e nessuno dei due era cercato

1. ⛔⭐ **`WT_DGRAM_RIMANDI_MAX` non misura quel che il suo commento dichiara.** `[R]`
   `w->dgram_rimandi` è un campo di `struct wt`, cioè **della connessione**: sale a ogni passata
   rifiutata e torna a zero solo su un successo. Il commento accanto dice *«quante passate di fila
   **il blocco in testa** è stato rimandato»* — ⛔ ma la testa nel frattempo è stata sostituita
   decine di volte. ⇒ **Non misura l'età del blocco: misura da quanto la connessione non spedisce
   nulla.** `[M]` Ed è per questo che il primo rifiuto è avvenuto **a finestra aperta**
   (`cwnd_left = 7 424`, e la riga stessa dice *«NON è la congestione»*).
   ⭐ E i rifiuti sono **a raffica, non sparsi**: fuori dalla raffica 0,004 %, **dentro 100 %** — 100
   rifiuti ogni 2,00 s = ogni blocco prodotto, per venti secondi. Non click sparsi: **venti secondi
   di niente**.
2. ⛔ **«L'audio non dev'essere affamato dal video» NON È SCRITTO DA NESSUNA PARTE.** `[R]` Cercato
   in `SPECIFICHE.md` (§10 e gli invarianti), `RCP.md` §6.3, `DECISIONI.md`, `CODER.md`: **niente**.
   L'unico posto in cui la domanda è decisa è il codice — `wt_scrivi():7286`, *«I DATAGRAM PRIMA
   DEGLI STREAM»*. ⇒ ⚠ **Una decisione presa nel codice e mai messa a verbale**, ed è precisamente
   il genere di cosa che questa fase esiste per scoprire.
   `[M]` E oggi vince **l'audio**: a desktop fermo il filo è tutto suo; sulla sessione vera col
   desktop in movimento tocca il **25-33 %** dei pacchetti.

### 20.2-quinquies ⛔ E UNA PREVISIONE DELL'AGENTE CHE NON HA RETTO — scritta com'è

`casa-cattiva`, scena col tono, stesso `netem`, cura spenta:

| codec | sul filo | spediti | rifiutati | ‰ | **copertura** |
|---|---|---|---|---|---|
| PCM | 1 024,5 kbit/s | 3 135 | **1 880** | **375‰** | 0,6088 |
| Opus | 366,3 kbit/s | 1 127 | **126** | **101‰** | **0,8803** |

⭐ La copertura sale **0,61 → 0,88** (+27 punti di audio che arriva davvero). ⛔ Ma il predicato
chiedeva *«Opus sotto 20‰»* e ha dato **rosso**: Opus divide il rifiuto per 3,7, **non lo toglie**.
⇒ **Il codec è la cura del costo, non del rifiuto.** Il confine è stato lasciato dov'era e il rosso
scritto nel banco, invece di ritarare la soglia dopo aver visto il numero.

### 20.2-sexies ⏳ La mezza cura descritta e non scritta — il `PADDING`

`dgram_scrivi_uno()`, righe **1613** e **1647**: `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING` va
**condizionato** al fatto che ci sia davvero un lotto da comporre (più di un datagram in coda, o byte
di video da infilare). Con **un** datagram solo e la coda video vuota il lotto GSO è di un pacchetto
e il riempimento **non compra niente** — costa 1 425 byte su 1 441. ⛔ **Non si toglie, si
condiziona**: il riquadro di `:1581` spiega perché c'è (un primo pacchetto corto fa collassare il
lotto GSO).

## 20.3 ⭐⭐⭐ IL DISALLINEAMENTO AUDIO-VIDEO — il numero regge, **la lettura no**, e si sente

`banchi/09-b85-*` · binario `64258ca4…`. ⛔ **E il metro è stato certificato prima di misurare
qualunque cosa**, in tre gradini, nessuno saltato.

**(a) sul file**, 7 sfalsi noti iniettati con `-itsoffset`: ritrovati **−700,0 · −300,0 · −100,0 ·
−0,0 · +100,0 · +300,0 · +700,0**. **(b) ricampionato a 40/s**, 4 fasi: bias **−2,3 ms**, ampiezza
**4,0 ms**. **(c) ⭐⭐ attraverso il prodotto vero**, lo stesso film con l'audio spostato di ±300 ms
noti, suonato nella sessione e ripreso dal filo:

| messo | ritrovato (n=23) | errore |
|---|---|---|
| **+300** | **+288,5** | −11,5 |
| **0** | **−12,6** | −12,6 |
| **−300** | **−310,8** | −10,8 |

⇒ **pendenza 0,9988, costante −11,6 ms.** Il metro ritrova quel che si sa di aver messo, col segno
giusto, su tutta la catena.

### 20.3-bis ⭐⭐ IL PRODOTTO È PULITO — **niente +331, niente +690, in nessun caso**

`[M]` 24 agosto (segno: **positivo = il suono esce DOPO l'immagine**, la convenzione di
`pagina.html` · `avvia_audio()`):

| caso | fps | Mbit/s video | **sfalso alla sorgente** | **sfalso in rete** | rete p90 |
|---|---|---|---|---|---|
| fermo | 40,1 | 0,30 | **−12,6** (n=23) | −5,8 | −3,9 |
| sotto carico | 35,1 | **106,5** | **−7,8** (n=22) | −14,7 | −16,6 |
| perdita 1 % | 36,5 | 0,30 | **−12,7** (n=22) | −6,1 | −9,8 |
| perdita 5 % | 16,2 | 0,60 | **−17,2** (n=10) | −19,1 | **−94,9** |

⇒ **Tutti e quattro entro ±6 ms dalla costante certificata.** Il prodotto marca i due flussi con lo
stesso orologio e li marca bene: **lo sfalso non nasce prima del browser.**

⭐ **E l'ipotesi «con la perdita peggiora» è smentita sulla mediana**, confermata solo sulla coda: a
5 % la latenza video p90 va a **118,5 ms** contro 23,6 dell'audio (gli stream ritrasmettono, i
datagram no) ⇒ **−94,9 ms**, cioè **l'audio che corre avanti**, non l'audio che resta indietro.
⚠ E metà delle claquette sparisce: **11 lampi su 20 click**.

### 20.3-ter ⭐⭐⭐ IL +331 NON È UN ARTEFATTO: **è il cuscino dell'audio, ed è scritto nel prodotto**

`[R]` `src/pagina.html` · `AUDIO_CUSCINO_MS()` `AUDIO_CUSCINO_MS = 250` · `:5564` `AUDIO_CUSCINO_MAX_MS = 600` ·
`:5761` `aoff = (perf − ist/1000) + CUSCINO + u`.

> ⇒ `AV ≈ cuscino + latenza d'uscita − ritardo di pittura`

A riposo 250 → **~331**; sotto carico la coda supera i 600 e `a.base` **si riàncora** (`:6152`) →
**~690**. ⭐ **I due numeri di §16.4 sono le due tacche del cuscino**, non due misure di un difetto.

⛔⛔ **E §16.4 legge il segno alla rovescia.** Scrive *«il suono precede l'immagine»*; il prodotto
dice *«positivo = il suono esce DOPO»*. ⇒ **L'audio è in RITARDO, non in anticipo** — e le due cose
hanno soglie percettive **diversissime**.

⚠ **E `AV` non può vedere la metà misurata qui**: elide l'`istante` del server da tutti e due gli
addendi. ⇒ Un prodotto con `AV` verde può essere desincronizzato, e viceversa. Le due misure **non si
sovrappongono**, e insieme dicono che lo sfalso vive **tutto dentro la pagina** — che è il posto dove
costa meno curarlo.

### 20.3-quater ⛔ SI SENTE — e la fonte è citata

**Rec. ITU-R BT.1359-1** (*Relative timing of sound and vision for broadcasting*, 1998), clausola g)
e Nota 1: *«detectability thresholds are about +45 ms to −125 ms and acceptability thresholds are
about +90 ms to −185 ms on the average, a positive value indicates that sound is advanced with
respect to vision»*.

⚠ **Il segno dell'ITU è l'opposto del nostro**: per loro positivo = suono in **anticipo**. Il nostro
+331 (audio **in ritardo**) è l'ITU **−331 ms**.

| | soglia ITU (audio in ritardo) | §16.4 a riposo (−331) | §16.4 sotto carico (−690) |
|---|---|---|---|
| **si nota** | −125 ms | ⛔ **2,6× oltre** | ⛔ **5,5× oltre** |
| **è accettabile** | −185 ms | ⛔ **1,8× oltre** | ⛔ **3,7× oltre** |

⇒ ⛔⛔ **Se il +331 è quel che l'utente riceve, si nota e non è accettabile.** ⚠ Che l'utente non
l'abbia giudicato sulla grana **non dice che non morde**: dice che quella scena non permetteva di
giudicarlo — ed è la **seconda** delle due letture tenute aperte in §16.4, non la prima.

⏳ **Che cosa resta**: la metà `AV` non è stata rimisurata (vuole il browser, e su quella macchina
Firefox non parte — §20.1-ter). Tutto quel che sta **prima** del browser è pulito; la conferma
diretta del 331 aspetta quello strumento.

> ### ⭐⭐⭐ E IL GIUDIZIO È ARRIVATO — **25 agosto 2026, fase 10**
>
> ⛔ *Il motivo per cui questo `[?]` era rimasto aperto era falso*: Firefox **non era rotto**, era
> `~/.cache -> /tmp` (§20.1-ter, **refutata**). ⇒ Tolto quello, il browser parte, e la prova si è
> potuta fare.
>
> ⭐ **E l'utente l'ha giudicata sulla scena più dura che ci sia** — un video **4K** dentro il
> desktop remoto, con la banda del suo tablet strozzata a **10 Mbit/s**, cioè **sotto il pavimento
> dichiarato**:
>
> > *«Il video mostra degli artefatti, ma è normale: siamo sotto le specifiche. Però **audio e video
> > fluidi e in sync**.»*
>
> ⇒ ⭐ **La metà `AV` del sincronismo ha il suo giudizio.** ⚠ **Non un numero**: un giudizio — il
> `[M]` dei **331 ms** e il termine di Opus restano `[?]`, e per quelli serve ancora lo strumento.
> ⭐ Ma la domanda che contava — *«all'orecchio e all'occhio, stanno insieme?»* — ha una risposta, ed
> è **sì**, presa dove il metro è l'utente (**I8**).
>
> `[M]` E accanto al giudizio ci sono i numeri della stessa scena, letti dal registro senza toccarla:
> **37,4 fot/s**, **3,20 Mbit/s**, ⭐ **coda vuota** — la banda **dimezzata senza perdere un
> fotogramma**. ⇒ `fasi/10-multi-tenant-e-il-budget.md` §10. ⚠ E il giro è a **PCM**: il termine di Opus non c'è dentro
(nel repo non esiste un decodificatore Opus, `07-b42-giudice.py` · `main()`).

⭐ **Il filmato c'è, ed è quel che serve all'utente per dare il suo giudizio**:
`/media/REMOTIX/tmp/09nr10/film/09-b85-claquette-calma-p000.mp4` (70 s, **34 attacchi**), coi gemelli
`-p300`/`-m300` a sfalso noto, e `-dura-` per il caso sotto carico. Il server **7973 è acceso**.

---

# §21 · ⭐⭐⭐ LA CHIUSURA — *24 agosto 2026*: le cure si accendono, e la parola «bistabile» cade

## 21.1 ⭐⭐ IL GIUDIZIO DELL'UTENTE SUL SINCRONISMO — **alla cieca, e il metro era il suo orecchio**

⛔ **La prova di §16.4 era fallita per un errore di disegno mio**: avevo chiesto un giudizio sul
sincronismo guardando **pura grana**, cioè l'immagine con meno appigli possibili. ⇒ Rifatta con la
claquette di §20.3 — un cartello che sbatte, **34 volte in 70 s** — e ⭐ **alla cieca, con tre
gemelli**, senza dire all'utente quale fosse quale.

| ordine | che cosa c'era **nel file** | il suo giudizio |
|---|---|---|
| 1° | audio **321 ms in anticipo** | *«perfetto»* |
| 2° | **allineato** (21 ms) | *«perfetto»* · *«il bip è in sincrono con il flash»* |
| 3° | audio **279 ms in ritardo** | ⭐ *«il flash è in anticipo rispetto al bip»* |

⭐⭐ **Ha riconosciuto il ritardo vero, con la direzione giusta, senza saperlo.** ⇒ Il suo orecchio è
**tarato** su questa scala, e i suoi giudizi valgono — che è precisamente quel che mancava a §16.4.

⛔ **E il verdetto è che il difetto non arriva.** Il filmato **allineato** gli è arrivato **in
sincrono**. Se il prodotto aggiungesse davvero i **+331 ms** di §16.4, quel filmato gli sarebbe
suonato **come il terzo** — riconoscibile, perché ha appena dimostrato di riconoscere 279 ms.
⇒ **Il ritardo che raggiunge l'orecchio è sotto la soglia che lui sa riconoscere**, cioè **< ~280 ms**,
e probabilmente molto meno.

⚠ **Che cosa questo NON dice**, e va scritto: fra il 1° e il 2° non ha visto differenza, e sono
distanti **321 ms**. ⇒ Dalla parte dell'**anticipo** la sua risoluzione è più grossa di 300 ms. Ma il
cuscino spinge dalla parte del **ritardo**, ed è lì che discrimina. ⚠ E il giro è a PCM: il termine
di Opus non c'è dentro.

⇒ ⭐ **§20.3-quater va letta con questo accanto**: il conto con la soglia ITU dice *«si sentirebbe»*
**se** i 331 ms arrivassero. `[M]` L'orecchio dice che **non arrivano**. Le due cose non si
contraddicono: §20.3 misura il cuscino **dentro la pagina**, e la latenza di pittura del video lo
compensa in gran parte — la parte che **nessuna delle due misure di ieri poteva vedere da sola**.

⛔ **E una correzione mia, presa e ritirata in tre minuti**: dopo i primi due *«perfetto»* avevo
concluso che `mpv` rimettesse in sincrono i flussi e che la prova fosse **nulla**. ⚠ Era una
conclusione affrettata su due dati: **il terzo giudizio l'ha smentita**. Lo scrivo perché la fretta di
dichiarare nullo uno strumento è lo stesso difetto della fretta di dichiararlo buono.

## 21.2 ⭐⭐⭐ «BISTABILE» ERA LA PAROLA SBAGLIATA — è **un innesco a rischio costante**

`banchi/09-b83-biforcazione.py` · `[M]` 24 agosto · casella `perdita-0,20` · **40 giri** a due durate
· binario `56c62bb0…` · cure spente.

**Prima campagna** (20 giri da 25 s): spirale **13 volte su 20**. Chiavi **0** in 7 giri, **≥ 5** in
13, ⛔ **nessun giro fra 1 e 4**: due rami, non una distribuzione larga.

⛔ **E il fatto che li distingue nei primi dieci secondi NON C'È: 43 prove su 43 negative**
(soglia Bonferroni 0,05/43, permutazione esatta sulla somma dei ranghi). ⭐ **E si è capito perché** —
gli istanti d'accensione (primo abbandono §5.1 a regime):

> **3,1 · 3,2 · 4,3 · 4,5 · 5,3 · 8,0 · 8,8 · 9,5 · 10,5 · 11,4 · 18,4 · 18,6 · 24,9 s**

⇒ **5 accensioni su 13 cadono DOPO i dieci secondi.** In quella finestra non c'era niente da trovare
perché in quei giri la spirale **non era ancora partita**. ⚠ La finestra corta era un limite del
**disegno**, dichiarato come tale e non attribuito al prodotto.

### 21.2-bis ⭐⭐ LA PROVA A DUE DURATE — la previsione regge

| durata del giro | spirale **osservata** | **attesa** dal rischio costante |
|---|---|---|
| **10 s** | **35 %** (7 su 20) | 31 % |
| **50 s** | **90 %** (18 su 20) | 92 % |

`[M]` λ = **0,0529 al secondo**. Le prove pre-registrate: **T3** — un solo λ spiega tutte e tre le
durate? **p = 0,53**, non si rifiuta. **T4** — c'è una forma nel tempo? **p = 0,055**, sopra la
soglia di 0,0125: nessuna forma.

> ⇒ ⭐⭐⭐ **Non sono due comportamenti fra cui il prodotto sceglie. È un innesco A SENSO UNICO: ogni
> secondo ha la stessa probabilità (~5 %) di accendersi, e una volta acceso non si spegne più.**

⛔⛔ **E la conseguenza è la cosa che conta**, perché tocca ogni numero di §17:

- tempo **mediano** perché si accenda: **13 secondi**;
- in **un minuto** di lavoro su quella linea è quasi certo;
- in **un'ora** — che è la durata vera di una sessione — è **certo**.

⇒ ⚠ **I nostri banchi girano venticinque secondi; le sessioni durano ore.** Ogni misura presa vicino
al bordo della perdita **sottostima, e non di poco**: quel che al banco appare come *«a volte
succede»* sul desktop vero è **succede sempre, aspetta solo il momento**.
⭐ E rilegge anche il *«è tutto fluido»* di §19.1: quei trenta secondi stavano dentro la finestra in
cui, statisticamente, spesso non si è ancora acceso. ⛔ **Non lo smentisce** — ma dice che **una
sessione lunga su quella linea andrebbe guardata prima di concludere**.

**Le ipotesi, una per una** `[M]`: la perdita non era la stessa ⇒ **esclusa** (0,165-0,255 % in
entrambe le famiglie) · l'avvio lento di CUBIC ⇒ **non verificata** (`ssthresh` lascia l'infinito a
~2 s in tutt'e due) · la scena ⇒ **esclusa** (prima chiave 58,44-58,88 kB in entrambe) · la soglia
dei tre pacchetti ⇒ **non verificata** · macchina carica ⇒ **esclusa** (CPU 5,1-6,5 % in tutti e 20).
`[R]` L'algoritmo è **CUBIC** (ngtcp2 1.25, `trasporto.c` · `accetta()` non tocca `cc_algo`) — ⚠ e la prova per
contrasto **non è stata fatta**: non è esposto da nessuna opzione.

⚠ **Che cosa non si sarebbe potuto vedere**, scritto prima: una separazione più piccola della
dispersione interna; una terza modalità rara (36 % di probabilità di non incontrarla); e ⛔ **niente
fra un secondo e l'altro** — `webtransport.c` · `linea_morta_giudica()` frena `rete_ciclo()` a una riga al secondo, quindi
dell'avvio lento si vede il punto d'arrivo, **non la corsa**.

## 21.3 ⭐⭐⭐ LE CURE SI ACCENDONO — e sulla linea sana **non peggiora niente**

*⇒ `DECISIONI.md` §3.1-septies. «Il prodotto cambia in meglio; questa fase era per rendere più solido
il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli.»*

**Il contratto — e per ciascuna una strada sola:**

| cura | predefinito | **unica** strada per spegnerla |
|---|---|---|
| soglia sulla coda video | **100 ms** | `--sgombra-soglia-ms 0` |
| regolatore del ritmo | **acceso** | `--niente-ritmo-adattivo` |
| linea morta | **accesa** (stallo 5 000 ms · silenzio 10 s) | `--niente-linea-morta` |
| sfratto del fantasma | **15 000 ms** | `--sfratto-ms 0` |
| silenzio dell'audio | **acceso** | `--niente-audio-silenzio` |

⛔ `--ritmo-adattivo` e `--linea-morta` **non esistono più**: chi li batte riceve un messaggio che
spiega il cambio e **uscita 2**, non un aiuto generico. ⛔ E il `-D AUDIO_SILENZIO_PREDEFINITO` è
**tolto**: due strade per accendere la stessa cura sono due numeri che divergono.
⭐ L'opzione dell'audio viaggia **negata** in coda all'`argv` del figlio — la strada di `--parlantina`
— perché il figlio è un `execve` con l'ambiente composto **da zero**.

⛔⛔ **Le righe d'avvio sono il verbale, e nessuna dice più «SPENTO (I6)».** Ognuna dichiara **stato ·
numero in vigore · che è il predefinito dal 24 agosto per decisione dell'utente · come si spegne**, e
`[M]` **il prezzo accanto**. Spente dicono *«SPENTA a mano … e NON è il predefinito»*.

### 21.3-bis ⭐⭐ LA PROVA CHE CONTA — la ferita di v1, cercata apposta

`banchi/09-b86-predefiniti.py` · porta 7980 · binario `14561dce…` · **29 casi di `--certifica`**.

- **(a) acceso di suo** ✅ — server lanciato **senza nessuna opzione**, e le cinque cure risultano
  attive ⛔ **lette dalle righe d'avvio del prodotto**, non dalla riga di comando;
- **(b) ognuna si spegne ancora** ✅ — cinque riavvii, una per volta; e i due nomi vecchi **rifiutati**;
- **(c) ⭐ il prodotto funziona acceso**, giro appaiato di 25 s a 1920×1080:

| braccio | fotogrammi/s | chiavi | quota delta | deriva finale |
|---|---|---|---|---|
| tutte **spente** | 39,60 | **0** | 1,0000 | 0,0 ms |
| ⭐ **predefiniti** | **39,69** | **0** | 1,0000 | 0,4 ms |
| `[M]` l'ancora di §17.6 | 39,85 | 0 | — | 0,1 ms |

⇒ **Nessun peggioramento**: −0,2 % contro le cure spente, −0,4 % contro l'ancora, **dentro il rumore
dichiarato del 5 %**. Zero chiavi, zero buchi, **zero scatti della linea morta, zero sfratti**.
⭐⭐ **Era la prova che poteva far ritirare tutto** — la ferita di v1 è esattamente «i numeri
migliorano e l'esperienza peggiora» — ed è verde.

⚠ **E due banchi si rompono per costruzione**, il che è voluto e va detto: `09-b79-cure.py` batteva
`--ritmo-adattivo`, `09-b84-audio-silenzio.py` appaiava **due binari** compilati diversi. ⭐ Adesso
il braccio spento si fa **dalla riga di comando sullo stesso identico binario**: un imputato in meno.
⏳ In cura.

## 21.4 ⭐⭐ LE CODE — e due delle tre si chiudono con un **no**

### 21.4-bis I due banchi rotti dalla modifica, e un difetto trovato rimettendoli a posto

`09-b79-cure.py`: bracci **rovesciati** — **A** = cure spente **a mano**, **C** = *nessuna opzione*.
⭐ Il guadagno è scritto nel commento: **il braccio che rappresenta il prodotto adesso è quello a cui
non si chiede niente**, e quindi non può promettere niente. `[M]` `--certifica` 21/21; giro vero su
`ritardo-30`: fps **38,15 / 39,61 / 39,78**, chiavi 0,2 / 0,0 / 0,0 %, **S′ verde**.

`09-b84-audio-silenzio.py`: da **due binari** a **uno**. ⭐ Due binari erano **due imputati** — se i
bracci davano numeri uguali le spiegazioni erano due (*«la cura non serve»* oppure *«i binari non
erano quelli che credevo»*); uno solo ne lascia una.
⛔⭐ **E semplificandolo è saltato fuori un difetto vero**: la riga del braccio **spento** adesso
contiene *«dal 24 agosto nasce ACCESA»*, e il banco cercava `"ACCESA" in dett` ⇒ **avrebbe letto
«accesa» su un braccio spento**, dando verde a due bracci sbagliati **proprio ora che quel predicato
è l'unica cintura**. Curato ancorandolo alle due frasi di stato.
`[M]` `--certifica` 31/31; giro `muto` (Opus, fermo): **557,5 → 5,7 kbit/s = 97,3×**, 1 248 blocchi
taciuti; giro `tono` (PCM): copertura **1,0000 → 1,0000**, purezza **1,000 → 1,000**, taciuti **1 su
5 002**.

### 21.4-ter ⛔⭐ `WT_DGRAM_RIMANDI_MAX` — **si tiene la grandezza, si cambia l'unità**

`[M]` Il numero che spiega tutto: `casa-cattiva`, 25 s ⇒ **2,2 milioni di rimandi**, cioè **~85 000
passate di scrittura al secondo** sotto carico contro **~200** a riposo. ⇒ Il tetto `4096` valeva
**~48 ms** in un caso e **decine di secondi** nell'altro. ⛔ E non era un fusibile, **era la
politica**: 2 258 blocchi buttati da quel tetto contro **9** dalla coda piena — il **99,6 %**.

⭐⭐ **La strada ovvia è stata provata e la misura l'ha rifiutata.** Timbrare ogni blocco e buttarlo
sull'**età vera**: `[M]` a 50 ms non scatta più di quanto scatti a 250, perché la coda tiene 8
blocchi = 40 ms di PCM e **la testa non è quasi mai più vecchia di 40 ms**. Prezzo di quel «non tocca
niente»: **+30 % di byte sul filo** (1 415 → 1 840 kbit/s, **rubati alla finestra del video**) per
**+11 % di blocchi utili** — il resto arriva già vecchio e **lo butta il cliente**.

⇒ Il campo diventa **`dgram_zitto_da`** («da quanto la connessione non mette un datagram in un
pacchetto») e il tetto **`WT_DGRAM_ZITTO_MAX_MS`**, in millisecondi. ⛔ E `4096` **non si converte con
una divisione**: è auto-referenziale — quante passate si fanno dipende da quanto si butta. `[M]` Col
prodotto 2,1 M rimandi, col tetto a 50 ms **20 M**. ⇒ Il valore si è **tarato sulla misura**, e il
verde è *«indistinguibile dal prodotto»*:

| tetto | spediti | butt. (coda) | rifiutati | kbit/s | utili | utili/filo |
|---|---|---|---|---|---|---|
| **il prodotto** (5 giri) | 2 912-3 242 | 14-16 | 1 753-2 084 | 1 312-1 447 | 1 223-1 315 | 0,40-0,44 |
| ⭐ **10 ms** | 2 947 | 16 | 2 039 | 1 286 | 1 246 | 0,435 |
| 5 ms | 2 999 | 15 | 1 995 | 1 327 | 1 246 | 0,424 |
| 50 ms | 3 955 | **797** | 263 | 1 743 | 1 390 | 0,360 |

**10 ms** (= due blocchi di PCM) sta **dentro la dispersione del prodotto su ogni colonna**.
⇒ ⭐ **La cura cambia quel che il numero vuol dire, non quel che il prodotto fa.** L'età vera del
blocco resta registrata (`dgram[].nato`) ma ⛔ **non decide**: finisce nella riga di registro accanto
al silenzio, **apposta per farsi smentire**.
⏳ Da riportare in `rcp.c`: il «conto finale» dice ancora *«rifiutati da ngtcp2»*, e adesso sono
*«buttati perché il filo era muto da N ms»*.

### 21.4-quater ⛔ IL `PADDING` — **NON fatta, e la diagnosi era sbagliata**

Scritta, costruita e misurata appaiata (desktop fermo col tono, `lo` liscio, stesso binario a meno di
quella riga):

| codec | riempimento | kbit/s | byte per pacchetto |
|---|---|---|---|
| Opus | sempre | 557,7 / 556,5 | 1 441 |
| Opus | condizionato | 556,9 / 555,8 | 1 441 |
| Opus | ⛔ **mai** | 556,4 | ⛔ **1 441** |
| PCM | sempre | 2 221,7 | 1 443 |
| PCM | condizionato | 1 988,0 | 1 292 |

⛔⛔ **Su Opus il guadagno è ZERO, non «piccolo»**: col riempimento **mai chiesto** il pacchetto resta
di **1 441 byte**. `[R]` **A riempirlo è `wt_scrivi()`**, che chiede il riempimento a *ogni* scrittura
di stream e chiude il pacchetto che il datagram aveva lasciato aperto con `WRITE_MORE`. ⇒ **Il
riempimento di una sessione ferma è dello STREAM, non del datagram**, e chi lo volesse togliere deve
andare lì.

⚠ Su PCM la condizione morde (**−10,5 %**) solo perché a 200 blocchi/s il datagram chiude il pacchetto
da solo — ma il PCM **non è quel che il prodotto negozia**, e col silenzio acceso a desktop fermo i
datagram sono **0,0/s**. ⇒ **Codice revertito**, e il verbale coi numeri resta nel riquadro
`MORE`/`PADDING` di `webtransport.c`: ⭐ una cura che non compra niente è **codice in più da
mantenere**, e va rifiutata con i numeri accanto invece che dimenticata.

### 21.4-quinquies ✅ E la decisione mai messa a verbale è ora in `SPECIFICHE.md` §10.1

⛔ *«Quando la finestra si stringe, l'audio passa davanti al video»* era una politica del prodotto
presa **nel codice** (`wt_scrivi()`) e **scritta in nessun documento**. ⇒ Adesso è `SPECIFICHE.md`
**§10.1**, con la ragione (i due carichi non si degradano allo stesso modo), il prezzo (banda tolta
al video proprio quando ce n'è poca) e il limite **per costruzione** (la coda dei datagram è lunga
otto ⇒ al massimo otto pacchetti passano davanti).
