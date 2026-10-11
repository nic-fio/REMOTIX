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
its slot until the **30 seconds of silence** of §5.3 — that is for the whole first round. It is the same
defect already written in `banchi/09-b71-sessione.sh` (`[M]` 23 Aug 08:06), which there is cured by sending
`TERM` and waiting; ⛔ **but between one bench and the next the wait is not there**, and nobody does it.

⚠ **Operating rule that comes out of it**: between two benches on the same user one **verifies that the slot
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
2. **less than the backstop with which a keyframe is already requested** — `WT_CHIAVE_RICHIESTA_MS` = 150;
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
backstop**: if it changes more than *N* times a second, the line becomes *«🔻🔺 RITMO PENDOLA»*, which
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
⇒ ~**60 lines/s = 21 MB/hour without `--parlantina`**, and **neither of the two has a backstop**.
⇒ ⛔ **The log is noisier when the line is worse, that is when it needs reading.**

⛔ **A third level (`--parlantina-ritmo`) is the wrong road**: it would put the I1 lines
behind a switch off by default, and ⛔ **a descent declared only when someone has switched on
a switch is NOT declared**. ⇒ Principle 2 and I1 impose `registro_dice()` for every
`🔻`/`🔺` line. ⭐ **What is needed is the backstop**, and the product already has **four working forms** of it,
all with the motivation written beside them: *only once* (`bool detto`) · *every N*
(`== 1 || % 100 == 0`) · ⭐ *when it changes by ≥ threshold* (**the shape of the `🔻`/`🔺` lines**) ·
⭐ *once a second, with the ZEROS inside* (**the shape of the periodic rate line**).

⇒ **The proposal, in four points and without a new level:**

1. the `🔻`/`🔺` lines at `registro_dice()`, **only when the value changes** ⇒ on a healthy session:
   **zero lines**;
2. a `ritmo:` line **once a second, always, with the zeros inside** — frames delivered ·
   skipped for credit · abandoned · bytes in the queue · value in force. **98 bytes/s per session =
   0.35 MB/hour**: **120 times less** than verbose mode;
3. ⛔ **a backstop on the three lines that under congestion come out at 28-60/s.** ⚠ And it cannot be put
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

## 14.1 ⭐⭐ THE CURE OF THE TEST CLIENT — and **how the real browser decides it**, verified

### The line changed

`banchi/01-b3-cliente.py` — the default of `--video-codec` was **`hevc,av1`**, now it is
**`h264`**. ⛔ **The cause is not a slip of tonight: it is a line left three days behind.**
On 20 Aug AV1 left the product (`DECISIONI.md` §1.13-ter) and the test client
kept declaring `hevc,av1` — ⇒ the server chose **HEVC** in every round, for three days.

### ⛔ AND DOES THE BROWSER DECIDE IT? — verified, not assumed

⭐ `pagina.html` does **not** ask the APIs for the codec, and it declares so at the top of the file: `[M]` 12 Aug,
on all seven HEVC strings `mediaCapabilities.decodingInfo()` and `canPlayType()` say
**yes** and the pixel does not arrive. ⇒ The page **paints a real probe and rereads the pixels**, and into the `CIAO`
goes only what it painted:

```
pagina.html:818   const PREFERENZA = ["hevc", "h264"];        ⛔ AV1 is no longer there
pagina.html:4672  const codec_buoni = PREFERENZA.filter((n) => …sondaggio…arriva);
pagina.html:4725  ["video.codec", codec_buoni.join(",")]
```

⇒ **On Firefox HEVC does not paint ⇒ the page sends `video.codec=h264` and that's all.** The client's new
default is **exactly that**, not an approximation.

### `[M]` THE PROOF THAT THE YARDSTICK CHANGED — *14:22:06-07 UTC*, verbatim lines from the log

```
14:22:06.637 rcp     negoziato video.codec=h264 video.profondita=8 audio.codec=pcm
14:22:07.782 video   primo fotogramma: (non letto) · 25450 byte · … livello 51, 2560x1080 ·
                     conversione … µs, … codifica … µs · H.264 8 bit via h264_vaapi
```

*(The conversion and encoding times of the line were removed after phase 18: the conversion is not proven
to be zero copy.)* *→ conversion (on the CPU) and encoding of the first 4K frame without the card: `fasi/18-senza-ffmpeg.md` §5.4.*
⚠ The 14:03 round, with the same binary and the old client, said
`hev1.1.6.L150.B0 … HEVC 8 bit via hevc_vaapi`. **Same server, same minute, two codecs.**

### 14.1.1 ⛔ THE EMPTY STRING — **it is a defect of the PRODUCT, not of the bench**, and it is worth less than it seemed

`[R]` of §13.5.2 verified line by line on the frozen tree `09c-src`:

```
codificatore.c:953   snprintf(c->stringa_codec, …, "hev1.%s%u.%X.%c%u%s", …)   ← HEVC
codificatore.c:1152  snprintf(c->stringa_codec, …, "av01.%u.%02u%c.%02d", …)   ← AV1 (dead code)
                     ⛔ and for H.264 THERE IS NO LINE: `avc1.` is not composed anywhere
codificatore.c:4065  c->conf.stringa_codec[0] ? … : "(non letto)"
```

⇒ ⛔ **Defect of the product**: `stringa_codec` is never composed under H.264, and the log
writes `(non letto)` and `«»`.

⭐⭐ **But it is NOT the R31 family, and this changes its seriousness.** The only use of
`stringa_codec` outside the encoder is `figlio.c` ⚠ *(the cited code is no longer there: to be reread)* and `:4780`, and they are **two log
lines**: the string **never leaves towards the browser**. The one the browser really uses is
composed by the page itself, from the level that **it** declares:

```
pagina.html:1182   return ["avc1.6400" + esa(idc), "avc1.64001f"];   /* idc da LIVELLO_DICHIARATO */
```

⇒ ⭐ **The defect is a BLINDNESS OF THE DIAGNOSIS, not a black screen**: under H.264 the log cannot
say which string would be needed, and whoever reads cannot compare it with the one the page
sends. ⛔ **And the blindness bites exactly where it is needed**: at 4K the server produces level **5.2**
(§13.6.2) while the page configures `avc1.640033`, that is **5.1** — and the line that would have made
the gap visible is the empty one.

## 14.2 ⭐⭐⭐ THE FIVE SCENES AT 2560×1080 IN H.264 — *14:23:08 → 14:26:26 UTC*

**The round**: port **7920**, binary `md5 162d2d10…` (`f90eb21`, no switch, glibc trap
off), user **`prova2`**, canvas **2560×1080**, **one single session** for all five
points — so the only variable is the scene. Cap **off**, `tc` **never touched** (`lo` verified
`noqueue` before and after, `enp7s0` never grazed). 30 s per point.

| scene | time | fps | ⭐ **H.264 video payload** | % of 20 | wire `lo` | bytes/frame | keyframes | abandons |
|---|---|---|---|---|---|---|---|---|
| **still** (no scene) | 14:23:08 | 0.00 | **0.000** Mbit/s | 0 % | 2.427 | — | 0 | 0 |
| ⭐ **REAL desktop** (`scena-utente.webm` at full screen) | 14:23:52 | 23.10 | **0.356** Mbit/s | **1.8 %** | 2.842 | 1 924 | 0 | 0 |
| **flat colour** (`pieno`) | 14:24:31 | 41.03 | **1.190** Mbit/s | 5.9 % | 3.717 | 3 624 | 0 | 0 |
| **halftone gradient** (`barra`) | 14:25:10 | 40.77 | **7.728** Mbit/s | 38.6 % | 10.45 | 23 695 | 0 | 0 |
| ⛔ **film with GRAIN** (the hard case) | 14:25:55 | 23.30 | ⛔ **44.574** Mbit/s | ⛔ **222.9 %** | 48.42 | 239 129 | 0 | 0 |

### ⛔⭐ THE ANSWER TO THE QUESTION THAT DECIDES

> **Does the hard case in H.264 exceed 20 Mbit/s?** ⇒ ⛔ **YES. 44.574 Mbit/s, that is 2.2 times the
> floor.**

### `[M]` THE TWO YARDSTICKS SIDE BY SIDE — and the distance is **not** a constant factor

| at 2560×1080, cap off | HEVC (§3.8, morning) | ⭐ **H.264** (14:2x) | ratio |
|---|---|---|---|
| still | 0 | 0 | — |
| real desktop | 0.204 | ⚠ **0.356** | ⛔ **1.7× UP** |
| flat colour | 1.179 | 1.190 | 1.01× |
| halftone gradient | 21.36 | ⭐ **7.728** | **0.36×** |
| film with grain | 58.668 | **44.574** | **0.76×** |

⛔⛔ **And this line is the new fact of the table**: H.264 does **not** cost «a third of HEVC», as
§13.5.1 suggested by measuring a single scene. It costs **36 %** on the halftone gradient,
**76 %** on the film with grain and ⛔ **170 %** — that is **more** — on the real desktop.
⇒ ⭐ **The ratio between the two codecs depends on the CONTENT**, and it is the same lesson as §3.8 («how many
pixels change predicts nothing») applied to the codec. ⚠ A conversion factor from HEVC to
H.264 **does not exist**: the old numbers are not converted, they are **redone**.

### ⭐ The positive control, and it is inside the table

The five points cover **three orders of magnitude** (0 → 0.356 → 1.19 → 7.73 → 44.57): if the bench
were blind they would give the same number. ⭐ And `barra` found again at **7.728** against the **7.920** of
§13.5.1, taken thirty-five minutes earlier with another session: **2.4 % gap**, that is the measurement
repeats.
⚠ **The `ferma` line says another thing worth reading**: **zero** video and **2.427
Mbit/s on the wire**. ⇒ With a still desktop **100 %** of what passes is QUIC + **the PCM audio**, which by
itself asks for 1.536 Mbit/s. `[?]` **On a narrow line it is audio that eats video, not the opposite** —
see 14.4.1, where at 3 Mbit/s video goes down to 5 fps and the wire stays at 2.4.

## 14.3 ⭐⭐⭐ §10.1 REDONE WITH THE RIGHT NUMBER — the contradiction **does not fall, it halves**

§10.1 compared two sentences: the study said *«no cap is needed»* on the real content,
the measurement said *«293 % of the floor»* on the hard case. ⛔ They were both **HEVC numbers**.

| | HEVC (what §10.1 said) | ⭐ **H.264** (what the user receives) |
|---|---|---|
| the user's **real content** | 0.204 Mbit/s = **1.0 %** | **0.356** Mbit/s = **1.8 %** |
| the **hard case** (film with grain) | 58.668 = **293 %** | ⛔ **44.574** = **223 %** |
| the distance between the two | **288×** | **125×** |

### ⭐ THE CONCLUSION, with the number and not with opinion

1. ⭐ **The first sentence holds, and holds better than before**: on the real desktop the product asks for
   **1.8 % of the floor**. A cap at 20 Mbit/s **has nothing to do** there, and §13.4 has already
   measured it (0.208 → 0.249, and the cure did not fall);
2. ⛔ **The second sentence holds too, and the change of codec does NOT save it**: the hard case asks for
   **223 %** instead of 293 %. ⇒ ⛔ **Moving to H.264 removes 70 percentage points and leaves the
   problem standing**: 44.6 against 20 is still **more than double**;
3. ⇒ ⭐⭐ **THE CONTRADICTION WAS NOT A CONTRADICTION, and it is decided**: the two sentences speak of two
   different contents, and both are true **on the same codec**. **The cap is needed, and needed only
   for the hard case** — that is it is exactly what §5.5 had designed: a parapet that on the
   real desktop does not notice it exists.
   ⛔ **And whoever wanted to throw the cap away now must answer this line**: *with what number does the
   film at full screen stay within 20 Mbit/s without it?*

## 14.4 ⛔⭐⭐ THE QUEUE THRESHOLD, tuned in the right direction — *14:27 → 14:35 UTC*

### 14.4.1 ⛔⛔ THE REQUESTED BENCH HAS NO POSITIVE CONTROL, and I say it before the numbers

The mandate asked for the sweep **on the real desktop**, and it is right: `barra` is synthetic.
⛔ **But on the real desktop there is nothing to tune, and I measured it instead of deducing it.**

`[M]` **14:27:48**, step on the real desktop in H.264, threshold **off**, squeeze at **3 Mbit/s** —
that is **a third** of what §13.8 had already tried at 10:

| s | 5-7 (wide) | **8** | **9** | **10** | **11** | 13-25 (wide) |
|---|---|---|---|---|---|---|
| frames | 29 | 21 | 13 | **5** | 5 | 27-29 |
| ⛔ **keyframes** | 0 | **0** | **0** | **0** | **0** | 0 |
| ⛔ **abandons** | 0 | **0** | **0** | **0** | **0** | 0 |

⇒ ⭐⭐ **At 3 Mbit/s — 15 % of the floor — on the real desktop the rate collapses from 29 to 5 fps and
the spiral DOES NOT START ALL THE SAME: zero keyframes, zero abandons.** §13.8 stopped at 5 Mbit/s and
found 3; here, even lower, there are **zero**.
⇒ ⛔ **A sweep of the threshold on this scene would measure zero against zero against zero**, that is
nothing. The bench has no stimulus, and a bench without stimulus gives *«the cure works»* for every
value. **I did not do it there.**

⭐ **And there is a second reason, and it comes from the new yardstick**: the objection of §13.8 against `barra`
(*«at 2560×1080 it costs 21 Mbit/s by itself, it is nobody's desktop»*) was an **HEVC** objection.
In H.264 `barra` costs **7.73 Mbit/s** (14.2), that is 39 % of the floor. ⚠ But the case that
**asks for** the cure is another one, and it is the real one: the **film with grain**, 44.6 Mbit/s.

### 14.4.2 `[M]` THE SWEEP, on the HARD CASE — film with grain, 2560×1080, H.264

**The round**, identical six times: 8 s wide → **3 s at 10 Mbit/s** → 17 s wide, `tc` only on `lo`
and only on 7920, guardian armed, `enp7s0` never touched (verified after each arm).
Server restarted at every arm, `md5 162d2d10…`, glibc trap off. The rows below are
**the 3 seconds of squeeze**, and the milliseconds are those the product writes by itself in the line
*«la coda del video passa SOPRA la soglia (… byte = N ms …)»*.

| arm | time | fps in the 3 s | ⛔ keyframes | ⛔ abandons | kbytes | cross. | ⚠ **ms of queue paid** | max `arretrato` |
|---|---|---|---|---|---|---|---|---|
| **off** | 14:29 | 6.0 | **8** | **8** | 6 111 | — | — | 0-1 by construction |
| **100 ms** | 14:30 | 6.7 | 8 | 10 | 6 507 | 8 | **136 – 397** | 3 |
| **200 ms** | 14:31 | 7.7 | 8 | 14 | 7 216 | 8 | **222 – 942** | 6 |
| **400 ms** | 14:32 | 5.7 | 6 | 8 | 5 930 | 7 | **414 – 643** | 8 |
| **800 ms** | 14:33 | 7.3 | **5** | 14 | 6 738 | 6 | ⛔ **856 – 1 321** | 7 |
| ⭐ **200 + `--ritmo-adattivo`** | 14:34 | 5.3 | 6 | ⭐ **6** | 5 521 | 7 | ⭐ **209 – 323** | ⭐ **2** |

### ⭐ THE PAIR THE USER MUST JUDGE, and the flat answer

> **At what value does the threshold keep P3's promise, and at what price in ms?**
> ⇒ ⛔ **NONE. Alone it does not get there at any value.** P3 asked for *keyframes ≤ 2/s*,
> *abandons ≤ 2/s* and *fps ≥ 25/s*: ⭐ keyframes come down into the promise at **400 ms** (2.0/s) and at
> **800** (1.7/s), ⛔ **abandons do not get there at any value** (2.7 – 4.7/s), and ⛔
> **frames do not even come close** (5.3 – 7.7/s against 25).
> ⭐⭐ **The only arm that brings abandons inside the promise is the PAIR**
> `--sgombra-soglia-ms 200 --ritmo-adattivo`: **6 abandons in 3 s = 2.0/s**, and it pays for them with
> **209-323 ms** of queue, that is **~264-378 ms from gesture to pixel** adding the 55 ms of the loop of
> phase 8.

### ⛔⛔ AND THREE THINGS THAT REFUTE WHAT §13.2.4 HAD CONCLUDED

1. ⛔ **«The improvement is monotonic» does NOT hold on the hard case.** Keyframes go down slowly
   (8 · 8 · 8 · 6 · 5) but **abandons wobble** (8 · 10 · 14 · 8 · 14) and so do frames
   (6.0 · 6.7 · 7.7 · 5.7 · 7.3). ⚠ One single round per arm: **a difference of one or two keyframes
   is within the noise, and I do not report it as an effect.** What is **outside** the noise is one
   thing only, and it is the price;
2. ⛔⛔ **THE PRICE GROWS FASTER THAN WHAT IT BUYS, and at 800 ms it is off the scale**:
   397 → 942 → 643 → **1 321 ms**. ⭐ The working point of §13.2.4 is confirmed a second time and
   on another scene (the queue settles **just above** the threshold, whatever number is chosen) —
   ⛔ but the consequence is that **raising the threshold buys 3 keyframes and sells a second and three tenths of
   delay.** ⇒ **The «raise it» direction of §13.2.3 is right only up to ~200-400 ms**: above that, the
   trade is the one `SPECIFICHE.md` §3.2 forbids in one line;
3. ⭐⭐⭐ **AND THE REGULATOR IS THE LEVER, NOT THE THRESHOLD.** Max `arretrato`: **3 · 6 · 8 · 7** with the
   threshold alone, ⭐ **2** with the pair — that is `WT_RITMO_POSTI = 2` **holds**, and the queue stops
   getting deeper. ⇒ At the same threshold of 200 ms, switching on the regulator **halves the abandons
   (14 → 6)** and **cuts the maximum delay from 942 to 323 ms**. ⛔ **The threshold alone is not the
   right lever; the pair is**, and it is what the mandate suspected.

⚠ **The red of §2 of the mandate is still standing and I declare it**: if the loop delay exceeded
55 ms + the threshold, the estimate of the draining underestimates. `[M]` here the measured queue reaches
**1 321 ms** against a threshold of 800: ⇒ ⛔ **at 800 ms the estimate IS already outside its range of
validity**, and it is one more reason not to go up there.

## 14.5 ⭐⭐⭐ P8 — THE RATE WITH A STILL SCENE, IN PAIRS: **GREEN** — *14:40:00 → 14:41:00 UTC*

**The round**: `banchi/09-b75-p8.py` (new), port 7920 with **both switches**
(`--sgombra-soglia-ms 100 --ritmo-adattivo`, read from the product's startup line, not deduced from the
command), canvas 2560×1080, H.264, **wide** line, **three pairs** still/moving of 8 s **alternated
in the same round**. The record is the line that `ritmo_ciclo()` writes **on the beat and not on the
frames**, one per second.

| | seconds | ⭐ **`arretrato` READ** | seconds with **ZERO** reads | maximum | ⛔ **descents** |
|---|---|---|---|---|---|
| ⛔ **STILL half** | 16 | **0 in all** | ⭐ **16 out of 16** | 0 | ⭐ **0** |
| ⭐ **MOVING half** | 27 | **1 072** = **39.7 per second** | ⭐ **0 out of 27** | 0 | ⭐ **0** |

⇒ ⭐⭐⭐ **GREEN, and on both points together**: in the still half the branch **was not travelled**
(«LETTO 0 volte», 16 lines out of 16) and the rate **did not go down**; in the moving half the loop was
travelled **1 072 times** and the rate **did not go down all the same**.
⛔ **And this is what «the counter is zero» could not say**: the two halves give the same zero
descents, and the `LETTO` lines say that **one earned it and the other did not**. Empty and forbidden
are distinct, which is the whole point of P8.

⭐ **And `massimo 0` in the moving half is the second fact**: on a wide line `arretrato` does not even reach
1. ⇒ The regulator is **a parapet that touches nothing**, as predicted (P7, S.5).

### ⛔ TWO BENCH DEFECTS FOUND ALONG THE WAY — and both gave «a plausible number»

1. ⛔ **The «moving» stage was marked AFTER the start.** `09-b68-scena.sh` launches the scene and then
   **sleeps 2 s** to verify it is alive: those 2.3 seconds, in which the scene **already paints**,
   ended up in the **still** half. `[M]` 14:37 — the still half came out with **26 lines instead of 18** and
   **147 reads**, and the bench said **YELLOW on a healthy round**;
2. ⛔ **The first second after the death of the scene still carries 22-40 reads.** It is not the product
   that does not stop: **killing the scene's process does not stop Mutter**, and the frames already
   composed keep arriving for about a second. ⇒ **2.5 s of guard** are thrown away after every
   change, **and it is declared**: counting them on one side or the other would attribute to the product a
   transient of the compositor. ⚠ **And the guard cannot hide the red that counts**: a
   descent with a still scene would fall in the **central** seconds, not on the edge.

## 14.6 ⭐⭐ 4K IN H.264 — *14:45:42 → 14:48:15 UTC*: **the missing number, and the cap MOVES**

**The round**: same 7920, same binary, **no switch**, canvas **3840×2160** verified in the
product's log (`SESSIONE: stato=1 tela=3840x2160`), `tc` never touched, 30 s per point,
one single session.

| at **3840×2160**, H.264, cap off | fps | ⭐ **video payload** | % of 20 | wire | bytes/frame | keyframes | ab. |
|---|---|---|---|---|---|---|---|
| ⭐ **REAL desktop** | 23.10 | **0.852** Mbit/s | ⭐ **4.3 %** | 3.351 | 4 607 | 0 | 0 |
| **flat colour** (`pieno`) | ⚠ **33.37** | 2.716 | 13.6 % | 5.259 | 10 174 | 0 | 0 |
| **halftone gradient** (`barra`) | **40.40** | 23.564 | **117.8 %** | 26.641 | 72 908 | 0 | 0 |
| ⛔ **film with GRAIN** | 23.27 | ⛔ **74.699** | ⛔ **373.5 %** | 79.279 | 401 320 | ⛔ **2** | ⛔ **2** |

### ⭐ 1. THE 41 FPS CAP **MOVES WITH THE SCENE** — and §13.6 could not see it

§13.6 had measured **41.25 fps** on `barra` and had concluded *«at 3840×2160 the product holds
~41/s»*. ⭐ With four scenes instead of one one sees that **it is not a cap, it is a point**: `barra`
**40.40**, ⚠ `pieno` **33.37** — that is **7 frames fewer on a scene that costs NINE TIMES
LESS bandwidth** (2.7 against 23.6 Mbit/s).
⇒ ⛔ **It is not bandwidth that decides the rate at 4K**, and it is not even the cost of encoding: it is what
**the compositor delivers**, and it is the same lesson as §3.1. ⚠ The two `video` points (23.1 and
23.27) **say nothing about the cap**: it is the clip itself that runs at ~23/s.
⇒ **`DECISIONI.md` must be corrected like this**: at 3840×2160 the product holds **33-41 fps depending on the
scene**, not 60 and not even «41».

### ⭐ 2. HOW MUCH 4K COSTS, and it grows **almost with the pixels** (but not on the hard case)

The pixels at 4K are **3.0×** those of 2560×1080. `[M]` the bandwidth:

| scene | 2560×1080 | 3840×2160 | ratio |
|---|---|---|---|
| real desktop | 0.356 | 0.852 | **2.4×** |
| flat colour | 1.190 | 2.716 | **2.3×** |
| halftone gradient | 7.728 | 23.564 | **3.05×** |
| ⛔ film with grain | 44.574 | 74.699 | ⚠ **1.68×** |

⭐ **The line that counts for the user**: at **4K** his real desktop costs **0.852 Mbit/s, 4.3 %
of the floor**. ⇒ ⛔ **4K is not a bandwidth problem**: it is a **frames** problem.
⚠ And the hard case grows **less** than the others (1.68× instead of 3×) because at 2560 it was **already** at the
limit of what the chain manages to produce.

### ⛔ 3. THE FIRST SIGN OF GIVING WAY ON A FREE LINE

The film with grain at 4K is the **only** point of the whole evening that produced **keyframes and abandons
with `tc` never touched**: 2 keyframes, 2 abandons, 1 keyframe withheld by §5.2 in 30 s.
⇒ ⭐ At **79.3 Mbit/s on the wire** the queue starts not emptying **even without any
throttling**. ⚠ It is the point where «wide line» stops being wide.

### ⛔⛔ 4. AND P9 REPRODUCES WITH THE NEW YARDSTICK — *14:42:50-51*, two lines one second apart

```
14:42:50.068 rcp     il client dichiara video.livello=5.1 … §4.3 vieta al server di emettere
                     un flusso PIU' ALTO di questo
14:42:51.328 figlio  §4.3 — LIVELLO PRODOTTO: 5.2 (nell'SPS e' 52) · stringa per il
                     decodificatore «»
```

⛔ **The server emits 5.2 where the client admits 5.1, and the program does not notice** — §13.6.2
was not a chance of that round: it repeats **every time** the canvas is 4K.
⚠ The «conversion + encoding» cap of the first frame was above the 40.40 of `barra`. *(The times were
removed after phase 18: the conversion is not proven to be zero copy.)* *→ in software: `fasi/18-senza-ffmpeg.md` §5.4.*

## 14.7 ⛔ AUDIO — **still NOT verified**, but the cause of two evenings is found and cured

⭐ **§13.7 accused the browser, and got the wrong defendant.** The line that closes the case, `[M]` 23 Aug
**14:49**, with the log created **first**, with the right uid and the right permissions:

```
⛔ Marionette non ha aperto la 2829 in 40 s.
   firefox vivo? ⛔ NESSUN PROCESSO
   il suo registro (/tmp/b74-ff.log): ⛔ VUOTO
```

⇒ ⛔⛔ **It was not Marionette not opening the port: it was Firefox not starting at all.**

### ⛔ 14.7.1 THE CAUSE, and it is THREE defects in a row — two mine, one of the system

1. ⛔⛔ **The launcher was a command line instead of a file.**
   `root("bash -c \"setsid nohup setpriv … firefox … &\"")`: `bash -c` puts the job in the
   background and **exits at the same instant**, `sudo` exits behind it and `ssh` closes the
   session — the process **dies in the race** before `setsid` has detached it.
   ⭐ **Cured**: `banchi/09-b74-ff.sh`, the same shape as `09-b72-video.sh` that has worked since the
   morning — a **FILE**, and the parent stays alive while the child detaches. ⚠ It is the third time
   today that the cure is *«a long script is shipped as a file»*;
2. ⛔ **`fs.protected_regular = 2`** (verified with `sysctl`): in a **sticky** folder like
   `/tmp`, **not even root** can open for writing a **world-writable** file belonging to
   another user — and that was exactly what the previous attempt had left there.
   `[M]` `cannot create /tmp/b74-ff.log: Permission denied` **as root**.
   ⭐ **Cured**: it is **deleted** and recreated (the permission belongs to the folder, not to the file);
3. ⛔ **And now Firefox starts, stays alive — and the test does NOT close all the same.** `[M]` 14:52:
   `firefox-esr 140.14.0esr`, three live processes with `--profile /tmp/b74-ff --marionette`,
   `MOZ_MARIONETTE=1` **read from `/proc/PID/environ`**, `marionette.port = 2829` in a `user.js`
   of **487 bytes** — and ⛔ **`ss -tlnp` shows NO listening socket of the Firefox process**,
   neither on 2829 nor on 2828.

### ⛔⛔ 14.7.2 AND THERE IS A SECOND WALL BEHIND THE FIRST, which the product's log proves

In the 7920 log **there is no request for the page from the browser**: after
`ascolto TCP su 0.0.0.0:7920` the only handshake is the test client's.
⇒ ⛔ **Firefox never asked for the page.** The certificate is **self-signed**, and without
`acceptInsecureCerts` — which is a function **of Marionette** — the browser stops
at the warning and does not issue the request.

⇒ ⛔ **The two walls are the same wall**: without Marionette the certificate is not accepted, and without an
accepted certificate there is no page. **I stop here and declare it**, as the rule says: two
attempts, then one moves on.

### ⭐ WHAT REMAINS TO DO, and the short road does not need Marionette

⭐ **The shape of the bench is right and now it is also proven**: the *before* and the *after* are **two
`pagina.html` files** served by the **same binary** (`md5 162d2d10…`), and the `md5` of the page is
read in the log (`d387c166…` for the old, `e010d615…` for the new). The record is sent by the
**page itself** every 5 s.

⇒ **It is enough for the page to open and to log in.** Two roads, in order of cost:

1. ⭐⭐ **Nic opens the page with his browser** (`https://192.168.0.2:7920/`, user `prova2`),
   accepts the certificate as he always does, and the server's log carries the three counters
   `vecchi` · `tardivi` · `fuori` by itself. ⛔ **No new tool is needed**;
2. ⚠ Or the certificate is taken out of the way before the browser: `cert_override.txt` in the profile,
   or a certificate the profile already knows. `[?]` **Not tried.**

⛔ **Until one of the two happens, cure 4 (the audio reorder) remains NOT VERIFIED**, and
it is the last of the six cures of 23 Aug without a number.

---

# §15 · ⛔ HOW THE MACHINE WAS LEFT — *verified at 14:56 UTC, not declared from memory*

| | |
|---|---|
| `tc` on **`lo`** | ⭐ `qdisc noqueue 0: root` — **no discipline** |
| `tc` on **`enp7s0`** | ⭐ `qdisc mq 0: root` — **never touched**, as per the rule |
| the `tc` **guardian** | ⭐ none: `.b68-guardiano.pid` is not there |
| **scenes, clients, browsers** | ⭐ **none** — neither `04-b30-scena`, nor `01-b3-cliente`, nor `firefox` |
| **ports** | ⭐ **7900 · 7910 · 7920**, the three from before, none more |
| ⚠ **and at 15:0x a FOURTH** | ⛔ **`7932` — it is NOT mine.** It appeared **after** I had finished, together with `banchi/09-b78-apertura.py` on the laptop: it is the bench of **another agent**. ⭐ I did not touch it. ⚠ I write it because «the machine was left like this» ages badly: ⛔ **the numbers of §14 are not dirtied by it** — the last `pulizia()` check of each of my rounds, up to 14:52:35, listed **only 7900 · 7910 · 7920** |
| **`core_pattern`** | `/media/REMOTIX/tmp/09c/core.%e.%p.%t` — **left**, it is the armed trap of §4.7 |
| ⭐ **the evening's log** | saved in `/media/REMOTIX/tmp/09c/registro-fase9-sera-PRIMA-DI-B74.log` (9 216 437 bytes) ⛔ **before** `09-b74` deleted `registro.log`: without that copy the numbers of §14.2-§14.6 would no longer be rereadable |

⭐ **And 7920 went back exactly as it was**, verified on the lines it writes itself:
binary `md5 162d2d10…` (`f90eb21`), page **`md5 e010d615…`** (the product's, not the one
of the audio *before*), **queue threshold 0 ms (OFF)**, **regulator OFF**, glibc trap
off, outside any user session.

⚠ **What I changed and do not put back, because it is the work**: `banchi/01-b3-cliente.py` now
negotiates **H.264** (§14.1). ⛔ It is the new yardstick, and whoever rereads an old number must look at
**which codec** the log of that round says.

---

## §16 · ⭐⭐⭐ THE HARD CASE ON THE REAL PATH — *23 Aug 2026, 15:20-15:30, with the user's browser*

⛔ **The first measurement of the phase taken with a real browser, on the real canvas, on the real network.** All
the earlier ones came from the test client on `lo`.

**The scene**: a clip of **pure grain** 2560×1080 at 30/s (`ffmpeg noise=alls=40:allf=t+u`, CRF 32,
90 s in a loop), played with `mpv --fullscreen` inside `prova`'s session on **7920**
(product of `f90eb21`+, **no switch on**, bandwidth cap OFF). The client is the user's
**Chrome** from 192.168.0.3. ⇒ It is the worst case a desktop can produce.

### 16.1 ⭐⭐ Bandwidth: **21.5 – 23.1 Mbit/s**, that is **107-115 %** of the floor

| | kbit/s | frames in 10 s | the largest |
|---|---|---|---|
| `[M]` 15:2x | **21 542** | 306 | 365 133 bytes |
| `[M]` 15:2x | **23 092** | 299 | 355 169 bytes |

⛔ **And this corrects §14.2 in the direction that counts**: the bench, with its synthetic scene, gave
**44.574 Mbit/s = 223 %** of the floor. The **real** hard case asks for **half** of it.
⇒ ⭐ **The bandwidth cap is still needed — but the margin to recover is 2-3 Mbit/s, not 25.**
⚠ And `[?]` remains **how hard the hardest possible case is**: pure grain is a synthetic upper
limit too; a real film compresses better.

### 16.2 ⭐⭐⭐ And the product HOLDS, with no cure on

`[M]` from the record the page sends by itself every 5 s, and from the child's log:

| | |
|---|---|
| frames | **7 125 delivered → 7 125 painted** · `salt 0` · `buchi 0` · `ord 0` |
| keyframes | ⭐ **1** in the whole round |
| audio | **35 169 received → 35 169 played** · `vecchi 0 · tardivi 0 · fuori 0 · rec 0 · dop 0` |
| audio queue | 238 ms |

⇒ ⛔ **No spiral, no abandon, no degradation** — with **all switches off**,
on the worst case, just above the floor. ⭐ It is the strongest confirmation phase 9 could
receive in the direction of decision §3.1-bis: **at 20 Mbit/s the product does not need to degrade.**

### 16.3 ⭐ The audio reorder cure (cure 4): **inert on the user's path, as predicted**

`[M]` `vecchi 0 · tardivi 0 · fuori 0` both at rest (4 936/4 936) and under the hard case
(35 169/35 169). ⇒ ⭐ **The half that counts for the product is proven**: the cure **changed
nothing for the user**. ⚠ **The half that bites — purity under reordering ≥ 0.95 — remains `[?]`**: it
can only be done by dirtying `enp7s0`, which is the interface of ssh and of the user's session, and it
was not touched.

### 16.4 ⛔⛔ AUDIO-VIDEO DESYNC GROWS UNDER LOAD — but **it CANNOT be judged by eye**

`[M]` the `AV` field of the page's record: **+331 ms** at rest → **+690 ms** under the hard case.
⇒ Sound precedes the image by almost **seven tenths of a second**.

⛔ **And here the bench was the user's eye, twice, and it said NO:**

> *«non posso sapere se c'è disallineamento se il video è incomprensibile»* — on pure grain, which
> offers **no reference** between what is seen and what is heard.
>
> *«ancora difficile giudicare il sync»* — on the same scene with a **grafted reference**: the whole
> screen flashes white for 0.12 s **once a second**, and at the same instant there is a
> **beep** (`sine=frequency=440:beep_factor=4`).

⛔ **Two readings, and both must be kept instead of choosing the comfortable one:**

| | |
|---|---|
| ⭐ **a desync that cannot be judged is a desync that does not bite** | and it is the product's yardstick: `LEZIONI.md` §7.3, *«when the user says it's fine, it's fine»* |
| ⛔ **or the INSTRUMENT is no good, and then the number has not been put to the test yet** | 690 ms on a full-screen flash **should** be seen. If they are not seen, either `AV` does not measure what we believe, or the flash gets lost in the grain, or the beep does not fall where I believe |

⇒ ⏳ **It remains `[?]`, and the road is an OBJECTIVE measurement, not another round by eye**: a reference
that can be **read** instead of judged — a flash on a **calm** background (not grain), captured
together with the sound, and the two instants compared on the wire. ⛔ And before measuring it the
**instrument must be certified**: `AV` must be compared with a **known and grafted** delay, or it is a number nobody has
ever verified. ⚠ It is the same shape as `DECISIONI.md` §7.19, where the ~400 ms desync has been open
**since August** and has never been closed.

⚠ **And a defect of the method, declared**: the test scene was **pure grain**, that is the case in which
the eye has the **fewest** possible holds. Asking for a sync judgement there was my error,
and the second scene did not correct it enough.

### 16.5 What stays on

`[M]` the scene and `mpv` **stopped** at 15:30. The two clips stay in
`/media/REMOTIX/tmp/09-scena/` (`duro.mp4` 209 MB, `duro-sync.mp4` 208 MB) — ⚠ on NVMe, **not** on the
rootfs in RAM: the first attempt had written them in `/home/prova`, which lives in RAM, and at CRF 18
it made **4.1 GB**. Deleted immediately.
⚠ Installed on the machine `mpv` and `ffmpeg` (the rootfs lives in RAM: after a reboot they must be put back).
⛔ **Firefox on the test machine does NOT start** for user `prova`: the profile is never
created (`~/.mozilla/firefox/` has only `Crash Reports` and `Pending Pings`). It is the same wall the
audio bench stopped at. ⏳ Not diagnosed.

---

# §17 · ⭐⭐⭐ THE BAD NETWORK — *23 Aug 2026, evening*, and **the target of the phase was corrected by the director**

> *«Comunque voglio farti notare una cosa: 30 mbps sono una connessione da metà anni 90. La vera
> sfida è misurare performance con reti che perdono pacchetti o pacchetti fuori sequenza, o
> presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**, `PIANO.md` phase 9.

⛔ **And the correction arrives with the phase half measured, with the proof that was needed.** §16 had just
shown that on the **real path** the worst case asks for 21.5-23.1 Mbit/s and the product holds it
**without degrading and with all the cures off**: 7 125 delivered → 7 125 painted, **one** keyframe,
zero abandons. ⇒ A bench that cannot make what it measures give way **is not measuring the right
quantity**. The pages that follow are the right quantity.

## 17.0 ⛔ The three quantities are not the same thing — and confusing them is the easy way of measuring wrongly

| | what it is | what it touches for us |
|---|---|---|
| **loss** | the packet does not arrive | **video** goes on QUIC streams, which retransmit ⇒ `[?]` it should be paid in **delay**, not in frames. **Audio** goes on datagrams ⇒ it is paid in **holes** |
| **out of sequence** | it arrives, but behind a newer one | ⭐ it is the missing condition of the **audio reorder cure** of 23 Aug, the only cure of the day whose useful half had never been verified |
| **jitter** | it arrives at irregular intervals | `[?]` QUIC can **mistake it for loss** and narrow the window for no reason. If it happens, the drop is **ours** |

⭐ **And `netem` on `lo` became a unique resource with a lock** (`banchi/09-lucchetto.py`):
the discipline is put on the **root** of the interface, so two benches that inject faults together
do not share the work — **the second cancels the fault of the first, and the first keeps
measuring believing it has it**. ⚠ It would not give red: it would give a plausible number. Ownership is
taken with `mkdir` (atomic even over ssh), it carries an **expiry written inside**, and whoever breaks an
expired lock **declares it**.

## 17.1 ⛔⛔⛔ VIDEO — the grid, and **it is not a degradation: it is a cliff**

`banchi/09-b76-rete-cattiva.py` · `[M]` 23 Aug 2026 · 25 s per profile · 1920×1080 · h264 ·
**free bandwidth** · ⛔ **all cures at their defaults, that is OFF** · binary `51b5994`.

| profile | lost % (probe) | burst | out of ord. % | **fps** | worst s | keyframes/tot | max drift | Mbit/s on the wire |
|---|---|---|---|---|---|---|---|---|
| `liscio` | 0.00 | – | 0.0 | **39.97** | 38 | 0/878 | 6 ms | 3.18 |
| `ritardo-30` ⭐**ref.** | 0.00 | – | 0.0 | **40.11** | 37 | 0/881 | 1 ms | 3.13 |
| `perdita-0,5` | 0.36 | 1.00 | 0.0 | **40.06** | 37 | 0/881 | 46 ms | 3.14 |
| ⛔ `perdita-1` | 0.94 | 1.01 | 0.0 | **9.56** | 4 | 117/209 | 142 ms | 4.00 |
| ⛔ `perdita-3` | 2.96 | 1.03 | 0.0 | **4.03** | 2 | **87/87** | 180 ms | 2.56 |
| ⚠ `perdita-5` | 4.78 | 1.04 | 0.0 | **3.35** | 2 | 73/73 | 157 ms | 2.01 |
| ⭐ `raffica-1` | 1.07 | **6.14** | 0.0 | **23.94** | **0** | 38/526 | **3 707 ms** | 2.99 |
| ⛔⛔ `raffica-forte` | 13.03 | 5.03 | 0.0 | **session DETACHED at 0.3 s out of 25** | – | – | – | – |
| ⭐ `riordino-25` | 0.00 | – | **68.0** | **40.03** | 38 | 0/880 | 11 ms | 3.27 |
| `jitter-5` | 0.00 | – | 85.3 | **39.30** | 32 | 2/864 | 17 ms | 3.52 |
| ⛔ `jitter-15` | 0.00 | – | 86.3 | **16.62** | 4 | 102/364 | 312 ms | **6.93** |
| ⛔ `jitter-30` | 0.00 | – | 73.2 | **8.07** | 2 | 110/175 | 475 ms | **6.26** |
| `duplicazione-1` | 0.00 (1.02 % dup) | – | 0.0 | **39.96** | 37 | 0/878 | 2 ms | 3.20 |
| ⛔ `casa-cattiva` | 1.71 | 1.02 | 93.8 | **7.78** | **0** | 73/169 | 609 ms | 3.51 |

⛔ **Thirteen red predicates**, and none mute. The fault was **verified as in place** on all 14
profiles, with **two legs that agree**: the qdisc's `dropped` and an independent probe
(`[M]` `loss 5%`: `dropped 101`, probe 101 out of 2000).

### 17.1-bis ⭐⭐ The three things the numbers say, and none was expected

1. ⛔⛔ **There is a cliff inside the first percentage point of loss**: from 100 % of the reference to
   **24 %**. It is not a curve, it is a **step**. ⚠ And no bandwidth test would ever have found it: at
   `perdita-1` the wire carries **4.00 Mbit/s**, that is **20 % of the declared floor**. The line is
   empty, and the product is on its knees.
   ⛔ ⚠ **The «0.36 %-0.94 %» range this line carried is WRONG, and §17.11 withdraws it**:
   it came from a cell (`perdita-0,5` at *40.06 · zero keyframes*) that **does not reproduce**.
2. ⭐⭐⭐ **At `jitter-15/30` the wire carries DOUBLE the bytes (6.9 against 3.1 Mbit/s) for ONE FIFTH
   of the frames, on a network that does not lose a packet.** `[M]` measured loss **0.00**.
   ⇒ It is the direct proof that **disorder is mistaken for loss**: retransmissions and keyframes
   that no loss asked for. The drop **is ours**, not the network's — and §3.1-ter had
   written it as `[?]` before measuring it.
3. ⚠ **The same average loss does LESS damage in clusters than scattered**: `raffica-1` (1.07 %, clusters
   of 6) holds 23.94/s against the 9.56/s of `perdita-1` (0.94 %, one at a time). ⛔ **But the price
   moves and gets worse**: a whole second at **zero frames**, and the drift at **3.7 seconds**.

### 17.1-ter ⭐⭐ THE MECHANISM — read in the server's log, not deduced

`[M]` on the same rounds: `abbandonato_in_coda` = `abbandonati` = `chiave_aspetta` **at every red
profile** (129 · 102 · 116 · 125 · 83), with `delta_non_spedito` at 550-800. And the **holes in the
succession of `numero`s** — the second leg, counted from the receiving side and independent of the
server's log — agree: 116, 86, 102, 109, 72.

⇒ **The chain is the spiral of §5.1→§5.2**, and it is the same face as the defect of 21 Aug:

> the wire delays → the send queue grows → §5.1 abandons the deltas → §5.2 kindles the debt
> → a **keyframe** is requested → the keyframe fills the window → **it starts again**

⛔ At `perdita-3` it does **87 keyframes out of 87 frames**: identical to the 144/144 of 21 Aug.

⭐⭐ **And the cure of this chain was already written, tested and OFF** — `--sgombra-soglia-ms` and
`--ritmo-adattivo`, behind a switch for invariant I6. ⇒ The grid above ran **with
the switches off**, and it is the reason why the paired test of the cures (§17.6) is the
mandatory sequel of this page and not an extra.

### 17.1-quater ⛔⛔ `raffica-forte` — **NOBODY detaches: DELIVERY stops**

⚠ The first reading of this cell said *«the session dies after 0.3 s out of 25»*. ⛔ **The word
was wrong, and a wrong word on a red is worse than a missed red**: it sends one looking for the
cause where it is not — here, a farewell that does not exist.

`[M]` 23 Aug, **four witnesses** (`banchi/09-b79-cure.py`): the client prints *«still
attached after 25.0 s: nothing dropped»* and closes **itself** at the end of the window · audio arrives for the whole
round (**696 datagrams, purity 1.0000**) · the server's log has **no** `CONGEDO`,
no `posto NEGATO`, no ban · the session had opened normally (`AMMESSO dopo 1 837 ms`),
which also rules out *«the handshake does not complete»* — consistent with §17.4. `IDLE_MS` is
30 000 ms and indeed has nothing to do with it.

⇒ **What stops is only the delivery of frames**: `[M]` **121 sent out of 981 captured, 860 NOT
SENT**, with `cwnd` nailed at **~10 KB** and the pacer refusing.

⛔ **The fact remains serious, and must not be downgraded**: a **live and mute** session is a still screen, and
for whoever watches it is indistinguishable from a dropped wire. ⚠ But it has **another name and another cause** — it does not
violate *«mai staccare»*, it violates the floor of the ladder (`DECISIONI.md` §2.1: 25 frames/s).
⇒ The predicate `p_niente_stacco` of `09-b76` measured **how long delivery lasted**, not **whether the
connection dropped**: the number was right, the word was not. ⏳ Being cured: the predicate is split in
two, because they are two facts with two causes.

⭐⭐ **And the cures change it**: in B and in C delivery lasts **all 25 seconds** (§17.6).

## 17.2 ⭐⭐⭐ AUDIO UNDER REORDERING — **the cure bites**, and now it is measured

⛔ It was the only cure of 23 Aug whose useful half had remained `[?]`, and for a stated reason:
*«to verify it one must dirty the network and I did not do it»*. The director's correction **is the
missing condition of that verification**.

⛔ **And first it was necessary to bring the cure into the benches' client**: it had been written **only
in `src/pagina.html`**, while `banchi/01-b3-cliente.py` still had the old rule. ⇒ Until
tonight **no bench could measure it**. Now there is `--audio-regola vecchia|nuova`, ⛔ with the
default **`vecchia`** and the verification that with it the counters and the **list** of blocks
delivered are identical to a literal transcription of the code of 22 Aug over five
successions: a client that changes the numbers already written is not an instrument, it is a variable.

`banchi/09-b77-audio-riordino.py` · `[M]` 23 Aug 2026 · port 7931 · 25 s per round · **two rounds
identical in everything except the rule**:

| profile | rule | **PURITY** | tone | coverage | on the wire | deliv. | vecchi | fuori | rec | dop | srv `dgram_falsi` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `liscio` | old | 1.0000 | 1.000 | 1.0000 | 4993 | 4993 | 0 | 0 | 0 | 0 | 0 |
| `liscio` | **new** | 1.0000 | 1.000 | 1.0000 | 4992 | 4992 | 0 | 0 | 0 | 0 | 0 |
| `jitter-2` | old | 0.7992 | 0.804 | 0.7993 | 4989 | 3987 | **1002** | 0 | 0 | 0 | 1062 |
| `jitter-2` | **new** | **1.0000** | 1.000 | 0.9982 | 4983 | 4983 | 0 | 1028 | 1028 | 0 | 115 |
| `jitter-5` | old | 0.6877 | 0.683 | 0.6854 | 4970 | 3418 | 1552 | 0 | 0 | 0 | 698 |
| `jitter-5` | **new** | **1.0000** | 0.995 | 0.9954 | 4970 | 4970 | 0 | 1620 | 1620 | 0 | 732 |
| `jitter-15` | old | 0.4350 | 0.370 | 0.3670 | 4214 | 1833 | 2381 | 0 | 0 | 0 | 1458 |
| `jitter-15` | **new** | **1.0000** | 0.846 | 0.8361 | 4177 | 4177 | 0 | 2392 | 2392 | 0 | 1458 |
| `riordino-25` | old | 0.8912 | 0.895 | 0.8912 | 4990 | 4447 | 543 | 0 | 0 | 0 | 1415 |
| `riordino-25` | **new** | **1.0000** | 1.000 | 0.9982 | 4982 | 4982 | 0 | 550 | 550 | 0 | 450 |
| `casa-cattiva` | old | 0.4013 | 0.261 | 0.2585 | 3192 | 1281 | 1911 | 0 | 0 | 0 | 1190 |
| `casa-cattiva` | **new** | **1.0000** | 0.648 | 0.6264 | 3120 | 3120 | 0 | 1837 | 1836 | 0 | 1190 |

**Six profiles out of six green, zero red, zero not judged.** `doppioni` **0** everywhere (a
duplicate here would mean the server sent it); `scartati_tardivi` **0** everywhere (the
safety net after the decoder never had to fire); `recuperati` repays the
`mancati` **one to one** (1028/1028, 1620/1620, 2392/2392) — that is the cure **does not accuse itself**
of losses it has instead recovered.

⭐ **And the cure stays honest**: `--certifica` carries two cases that would give it **red** if it were not —
purity 0.999 **with** `fuori_ordine` at zero (it would mean the profile does not bite and the green is
chance), and the counter-proof that the new rule **still throws away** the block that really arrived too
late. A cure that kept everything would not be a cure: it would be the removal of a check.

### 17.2-bis ⛔⛔ THE `[M]` OF «0.175» — the count holds, **its purity does not**

`src/pagina.html` · `avvia_audio()` carried: *«jitter ±2 ms ⇒ purity 0.175, 1 004 discarded out of 4 989»*.
`[M]` tonight, same profile: **1 002 thrown away out of 4 989 on the wire**. ⇒ The **same denominator**,
two blocks of difference: the **count** of that `[M]` is solid.

⛔ **But its «purity 0.175» is comparable with nothing**, and it was stopped before it
became a triumph. The fraction the page benches use is `suonati/ricevuti`
(`09-b74:300`), and `a.ricevuti++` sits **after** the discard branches (`pagina.html` · `avvia_audio()`): the denominator
counts **only the survivors**, so that ratio is ~1.000 **with both rules**, on
even a destroyed succession. ⚠ It is true in the code **before** and **after** the cure, verified on
`f90eb216^`: where that 0.175 came from **is not known**, and it is a number whose
definition is unknown.

⭐ ⇒ The bench's quantity is **`purezza = consegnati / sul filo`**, with the denominator counted
**before** the screening, and the expected value is a **declared border** (0.90 / 0.80 / 0.60), not that point.
`purezza_pagina` is printed beside it **only for comparison**, with a note saying it is blind.

### 17.2-ter ⛔⭐ THE RED THAT BELONGED TO THE BENCH — and the cure of the predicate

`casa-cattiva` gave red: the client counted **2 183 `mancati` out of 4 996, 43.7 %**, with `netem`
at **2 %**. ⛔ It was not the network: the server's log said **1 823 blocks REFUSED by ngtcp2** —
never put on the wire, congestion window closed at 40 ms of delay. `mancati` is built on the
jumps of `istante`, and **a block never sent leaves the same jump as a lost one**.

⇒ The predicate was rewritten **on both ends**: `spediti dal server − sul filo del cliente` =
**67 lost on the network, 2.10 %**, against the 2 % asked of `netem`. ⭐ It is R13 in pure form — a
number that seemed to measure the network and measured us.

### 17.2-quater ⚠⚠ AND BEHIND IT THERE IS A FACT OF THE PRODUCT THAT HAS NOTHING TO DO WITH THE CURE

`[M]` the audio blocks **refused by ngtcp2**, that is produced and never put on the wire: **4** on
`jitter-2`, **819** on `jitter-15`, **1 823** on `casa-cattiva` — ⛔ **36 % of the audio produced
does not reach the wire**. ⇒ It is also the reason why on `jitter-15` and `casa-cattiva` the *coverage*
stays at 0.84 and 0.63 **despite having purity 1.0000**: the receiver delivers everything that reaches it,
but **the transport does not make everything reach it**. ⏳ Open, and it is not a defect of the cure: it is the same
congestion window that in video produces the spiral.

## 17.3 ⭐⭐⭐ TWO NEW WITNESSES IN THE SERVER — and one measures REORDERING

⛔ Before tonight the log **could not say whose fault it was**. A late frame
could be a packet lost and resent, the window closed, us having held it or us
having abandoned it: the last two were counted, **the first two were not**.

**1 · the `rete-quic` line** (`src/webtransport.c`, `rete_ciclo()`) — at most one per second, and
**silent if the counters are still and the judgement has not changed**:

```
rete-quic 192.168.1.9:52344 da_ms=1002 persi=7 persi_d=3 byte_persi=9856 ... cwnd=48000
cwnd_left=0 ssthresh=32000 involo=47180 srtt_us=41230 latest_us=52980 rttvar_us=11400
min_rtt_us=22100 coda_rete_us=19130 pto_us=132000 dgram_persi=… giudizio=⛔ la linea perde
```

⚠ Three choices a bench must know: `giudizio=` is **the last field** and its value runs to the
end of the line; the rtt is in **microseconds** (on a local network `rttvar` rounded to ms would be 0, and
would hide precisely the jitter that is the target); `da_ms` is the **real** interval, and the `_d` fields
hold over it — calling them `_1s` would have been a number that looks measured and is not.

The **judgement** has three values and the rule is written: `persi_d > 0` ⇒ `⛔ la linea perde` (first,
because the closed window is almost always the **consequence** of loss, and inverting the cause would
hide it behind its effect); otherwise `cwnd_left == 0 && cwnd > 0` ⇒ `⚠ la finestra e'
chiusa`; otherwise `-- niente da segnalare`. ⛔ The judgement **speaks neither of jitter nor of reordering**,
on purpose: ngtcp2 does not give those numbers, and deducing them from `rttvar` would have required a **threshold**, that is a
decision.

**2 · ⭐⭐⭐ `dgram_falsi` — reordering, measured from the server side.**
`[S]` `ngtcp2.h:3442`, on the `lost_datagram` callback: *«Note that the loss might be spurious, and
DATAGRAM frame might be acknowledged later»*. ⇒ Same `dgram_id` seen first as **lost** and then
as **acknowledged** = packet **arrived out of sequence**, declared lost by the three-packet
threshold and acknowledged afterwards.

⛔ Until tonight `ngtcp2_callbacks` (`src/trasporto.c` · `ngtcp2_callbacks`) registered `recv_datagram` **and nothing else**:
incoming datagrams were counted (finding B-10), **outgoing** ones — that is audio — vanished
into the wire without leaving a trace. *«The audio did not arrive»* and *«it arrived and the client threw it
away»* had the same face, and it is the same defect as then from the other direction.
⛔ And they are registered **as a pair**: `lost_datagram` alone would count reorderings as **losses**,
that is it would give a number **higher than the true one** and without saying so.

⚠ **The price, declared**: it holds **on datagrams only**, that is on audio. QUIC streams do not
have an identifier per piece, and this road **does not exist** there — on video reordering remains
without a direct witness.

### 17.3-bis ⛔ What ngtcp2 1.25 does NOT give, said loudly

- **retransmitted packets do not exist** `[S]`: QUIC does not retransmit packets, it retransmits the *frames*
  inside new packets, and there is no resend counter. `pkt_lost` (the packets
  **declared** lost) is as close as one gets;
- **reordering on streams is not counted** `[S]`: no field, no callback, and the three-packet
  threshold ngtcp2 uses internally without exposing it. ⇒ There `rttvar` remains the only clue;
- **`delivery_rate` does not exist** `[S]`: bandwidth stays estimated from `cwnd`/`smoothed_rtt`;
- ⛔ **the `reordered` counter of `tc` does not exist on this machine** `[M]`: iproute2 6.15.0, the
  `netem` block prints only `Sent/dropped/overlimits/requeues/backlog`, and with `reorder 25% 50%`
  on only `requeues` moves. ⇒ Reordering was measured with **three concordant witnesses** —
  a numbered UDP probe through the same `netem`, the overtakings counted on the client's JSONL, and
  `dgram_falsi` from the server — not deduced.

## 17.4 ⭐⭐ THE HANDSHAKE UNDER LOSS — **the `[M]` of 10 % was a bench defect**

`banchi/09-b78-apertura.py` · `[M]` 23 Aug 2026 · 10 rounds per step · loss **read** from
`tc -s qdisc` · up to `AMMESSO` (QUIC + extended CONNECT + `CIAO/ECCOMI` + `CREDENZIALI/AMMESSO`):

| loss requested | real loss | opened | QUIC median | total median | total max |
|---|---|---|---|---|---|
| 0 % | – | **10/10** | 7.8 ms | 1 014 ms | 1 116 ms |
| 5 % | 8.2 % | **10/10** | 7.8 ms | 1 078 ms | 1 318 ms |
| 10 % | 9.5 % | **10/10** | 10.9 ms | 1 103 ms | 1 219 ms |
| 15 % | 15.2 % | **10/10** | 111.5 ms | 1 281 ms | 1 708 ms |
| 25 % | 24.3 % | **10/10** | 211.9 ms | 1 299 ms | 1 738 ms |

⭐ **The session always opens**, even at 25 %. **The network costs 285 ms between 0 and 25 %**; the
second that one sees **is not the network**, it is the fixed delay of §4.4-bis against whoever tries passwords.
The handshake maxima sit at 212 and 613 ms — **one and two PTOs**.

The five hypotheses, all refuted one by one: the client does not give up (**0 rounds out of 70**
exceeded its cap of 8 s); the ban has nothing to do with it (`src/rcp.c` · the count of PAM verdicts counts only PAM verdicts on
`CREDENZIALI`, and a handshake does not get there); ngtcp2 retries (`handshake_timeout` stays
`UINT64_MAX`, `trasporto.c` · `accetta()`); the `netem` is not applied twice (the two filters take the two
**directions**, so a **round trip** pays `1-(1-p)²` and a **datagram**, which goes one direction only, pays `p` —
`[M]` 3 235/3 607 = 89.7 %).

### 17.4-bis ⛔ THE PREDICATE THAT COULD NOT GIVE RED — R13 again, in `07-b64-rete.py`

```python
def a_non_si_apre(n):
    return _p(n["ricevuti"] == 0, "nessun datagram: la sessione non si apre")
```

⛔ `01-b3-cliente.py` · `_capsula_chiusura()` prints `[audio] ricevuti 0` **also from the `except` branch**, before
re-raising. ⇒ **Every** way of failing — a `CONGEDO`, an expired cap, a `NameError` of the bench —
made that step pass **green**. The bench was not measuring *«it does not open»*: it measured *«I have not
received»*, and the two things have the same face.

⛔ **And a second defect in the same file**: `guasta([])` calls `rimetti(False)`, which calls
`guardiano_disarma()`. The profile `0-liscio` is **the first**, so it disarmed the guardian armed
two lines earlier, and the **eight following profiles ran without a safety net**.

⏳ **The two cures are written and NOT applied**: `07-b64-rete.py` is imported by the benches that are
running at this moment, and changing a signature of it in the middle of a measurement would be the defect this
section describes.

## 17.5 ⛔⛔ THE GHOST — *«you already have an active session elsewhere»*, and for the user it is **false**

⭐ It is the product fact found behind §17.4, and on the target of the phase.

The only way an opening really fails under loss is `ATTACCA` → `CONGEDO(0x0F)
GIA_ATTIVA_REMOTA` (`[M]` 5/10 at 10 % loss). The log says: *«place DENIED … it is occupied by
another client of this same user»*.

⛔ **The account closes without `netem`**, because a **lost** goodbye and a goodbye **never said** are the
same fact: with the client killed with `-9`, `[M]` **11 refusals in a row, and the slot becomes free again at
+30.5 s** — that is `SILENZIO` (`src/rcp.c` · `SILENZIO`, 30 000 ms).

⚠ **The sentence the client builds is false for whoever reads it**: that session is **his own**, and it
died a moment before. And the box of `src/rcp.c:229-233` declares that that clock *«makes
the case "the phone died in a tunnel" disappear»* — ⛔ it does not make it disappear: it makes it **last thirty
seconds**, and packet loss is precisely what makes it **normal** instead of rare.

**The proposed cure, NOT written — it is a change of policy of §8.2 and the user decides it:** in
`src/rcp.c`, branch `POSTO_OCCUPATO` of `rcp_attacca()` (lines 2605-2616), before dismissing with
`0x0F` look at the occupant's `ultima_vita`: if it has been silent for more than a short threshold (~3 s) **while
another client of the same user is asking for the slot**, evict it. §8.2 says *«no client
attached and **alive** is ever ousted»* — the occupant here is attached but **not alive**, and today
the only clock that distinguishes it is the 30 s one. `torna_a_parlare()` (`rcp.c` · `drena()`) already handles
the evicted one coming back. ⛔ It would not touch `SILENZIO`, which stays 30 s for everything else.

## 17.6 ⭐⭐⭐ THE TWO CURES, PAIRED — **the spiral switches off, and only with both**

`banchi/09-b79-cure.py` · `[M]` 23 Aug 2026 · binary `eee17f40…` from the **working tree** ·
25 s per cell · 1920×1080 · h264 · one round per cell. ⛔ Every arm verified from the **product's
startup lines**, not from the command line (a switch believed on and not on would
give a pairing without difference, that is a green). The fault verified by the probe at **every**
cell.

- **A** = the defaults, that is **cures off**. ⛔ Remeasured, not taken over from §17.1: those numbers
  come from another binary and another time.
- **B** = `--sgombra-soglia-ms 100` — the queue threshold alone.
- **C** = `--sgombra-soglia-ms 100 --ritmo-adattivo` — threshold **plus** rate regulator.

| profile | arm | fps | worst s | **keyframes %** | final drift | **max drift** | Mbit/s wire |
|---|---|---|---|---|---|---|---|
| `ritardo-30` ⭐**healthy** | A | 39.85 | 36 | 0.0 | 0.1 | 8.9 | 7.55 |
| | B | 40.19 | 37 | 0.0 | 0.2 | 5.8 | 7.60 |
| | C | 39.63 | 36 | 0.0 | 0.9 | 6.1 | 7.53 |
| `perdita-1` | A | 11.96 | 5 | **51.7** | −2.4 | 76.5 | 3.43 |
| | B | 32.13 | 17 | 6.4 | 23.2 | 107.8 | 4.84 |
| | **C** | **32.85** | 21 | **0.0** | −1.6 | 99.3 | 5.11 |
| `perdita-3` | A | 7.34 | 5 | **88.1** | −40.0 | 53.4 | 2.17 |
| | B | 20.63 | 11 | ⛔ 23.8 | 32.9 | 139.3 | 2.90 |
| | **C** | 19.63 | 11 | **0.2** | −62.2 | 165.7 | 2.79 |
| `jitter-15` | A | 10.76 | 6 | **59.2** | 11.7 | 102.1 | 3.48 |
| | B | 25.88 | 9 | ⛔ 12.8 | −65.7 | 64.0 | 8.06 |
| | **C** | 21.48 | 15 | **0.0** | 53.8 | 168.4 | 6.63 |
| `jitter-30` | A | 8.56 | 5 | **73.1** | 6.7 | 115.6 | 2.55 |
| | B | 20.25 | 10 | ⛔ 19.9 | −5.0 | 277.0 | 5.77 |
| | **C** | 16.68 | 12 | **0.0** | −116.0 | 180.8 | 4.96 |
| `casa-cattiva` | A | 8.28 | 3 | **72.0** | −71.5 | 295.3 | 2.21 |
| | B | 14.37 | 6 | ⛔ 33.6 | 152.7 | 238.4 | 3.01 |
| | **C** | 13.86 | 4 | **5.6** | 102.2 | 284.2 | 3.38 |
| ⚠ `raffica-forte` | A | *delivery dies at **4.4 s** out of 25* | | | | | |
| | B | 4.25 | **0** | 44.6 | 24.9 | **7 756** | 0.59 |
| | C | 4.18 | **0** | 4.4 | 2.1 | **4 521** | 0.78 |

### 17.6-bis ⭐⭐ The four facts

1. ⭐⭐⭐ **The spiral switches off — but only with arm C.** The keyframe share goes from **51.7-88.1 %**
   to **0.0-5.6 %** on all five red profiles. ⛔ **The threshold alone (B) is not enough**: it leaves
   12.8-33.6 % keyframes on four profiles out of five.
   ⭐ **And the why is read in the server's counters**: in C, on `raffica-forte`,
   `delta_non_spedito` **988 → 6** and `chiave_aspetta` **32 → 0**. The threshold stops *throwing away*, but
   the debt of §5.2 keeps **kindling**; the regulator prevents it because the frame
   **does not leave at all**. ⇒ It is the experimental confirmation of the mandatory order declared in §6: the
   threshold is the **prerequisite** of the regulator, not an alternative.
2. ⛔⭐ **The healthy line pays nothing** — and it was the predicate worth more than all the others.
   39.85 / 40.19 / 39.63 fps (one percentage point, within the declared 5 % noise), **zero
   keyframes** in all three arms, final drift 0.1 / 0.2 / 0.9 ms. ⇒ The cures **have no
   regime cost**: they are mute until they are needed, which is precisely what I1 demands.
3. ⭐ **The rate comes back by 1.7 to 2.8 times** on every red profile. ⚠ And B almost always gives **more**
   frames/s than C: ⛔ they are not «worse and better», they are **more frames with more keyframes** against
   **fewer frames, all deltas**. Whoever compared only the frames/s column would choose B
   and take the spiral home.
4. ⭐⭐ **And the bytes on the wire RISE** (3.48 → 8.06 Mbit/s at `jitter-15`): ⇒ **the line was not saturated,
   it was wasted.** It is the other face of §17.1-bis point 2 — there double the bytes for a fifth of the
   frames, here double the bytes for **double** the frames.

### 17.6-ter ⚠ THE PRICE, and the two numbers are given without choosing

**Maximum drift**, on the five ordinary profiles: from **−38 to +161 ms** compared to A (⭐ on
`casa-cattiva` and `jitter-15` arm B even makes it **drop**). **Zero on the healthy line.**

⛔ **On `raffica-forte` the price explodes: 4.5-7.8 seconds.** There C **is not obviously better than A**:
it is *an image that moves with five seconds of delay* against *a still image*. ⚠ This
document gives the two numbers and **does not choose**: the choice between image and delay is the user's
(`DECISIONI.md` §0.1, invariant I6), not a measurement's.

## 17.7 ⛔ THE BENCH DEFECTS FOUND TONIGHT — all of the form «silence instead of red»

| where | what | outcome |
|---|---|---|
| `07-b64-rete.py` | `a_non_si_apre` green on any way of failing | ⭐ **cured** and run again (§17.4-bis, §17.9-bis) |
| `07-b64-rete.py` | `0-liscio` disarms the guardian for the eight profiles after it | ⭐ **cured**, `[M]` guardian still alive after `guasta([])` |
| `07-b64-rete.py` | `spediti_dal_server` at `None`: `None == 0` is false ⇒ green on a round in which the server's end had not been read | ⭐ **cured**: now it is mute (§17.9-bis) |
| ⛔ `07-b64-rete.py` | the «final count» line arrives **29 s late** when the pacer has a queue ⇒ the next round reads **the count of the previous round** — and the slot still occupied makes it die of `GIA_ATTIVA_REMOTA` | ⭐ **cured** with `registro_posato()` (§17.9-bis) |
| `09-b70-ritmo.py` | `sudo -S` covers only the **first** command of the chain ⇒ the §11.1 reader was not written | ⭐ **cured** with `catena_root()` (§17.9-ter) |
| `09-b70-ritmo.py` | a trailing `< file` **steals stdin from `sudo -S`** ⇒ `righe_registro()` returns 0 in silence, and `attese_a_vuoto` becomes cumulative since startup — that is the column on which I1 decides whether to refuse to judge | ⭐ **cured**, `[M]` 1 604 for the round against 4 041 cumulative |
| `09-b70-ritmo.py` | `01-b4-validatore.py` is not shipped by the ground ⇒ empty journal ⇒ **red on «does not detach» on a session alive for 797 frames** | ⭐ **cured**: the ground verifies it, the bench refuses |
| `09-b76` | ⛔ `p_niente_stacco` measured **the duration of delivery** and called it **detach** | ⭐ **split in two** (§17.9-quater) |
| `09-b79-cure.py` | the wrapping of `root()` skipped the cure of the underlying one | ⭐ **cured**, and `[M]` **no number was dirtied** (§17.9-sexies) |
| `09-b76` (while working) | ⛔ **`tc qdisc change` is sticky**: a `reorder` set for one profile stayed on in the four after | cured: the bench **rereads** the installed rule and gives red if it carries a verb not asked for |
| `09-b77` (while working) | the regexes looked for the **internal** names of the counters while the client prints other names ⇒ `None` on everything, no error | cured, and `--certifica` now tests the regexes on the client's **real output** |
| `09-b77` (while working) | `mancati` counts as lost also blocks **never sent** | cured: the predicate works **on both ends** (§17.2-ter) |

## 17.9 ⭐⭐ THE ROUND OF CURES TO THE BENCHES — *23 Aug, night*, and four more came out

⛔ **Seven bench defects out of nine found tonight, and all of the same form: «silence instead of
red».** The cures were applied and **every bench was run again**. What follows is the
sequel, and it is worth reading because **two of the four new ones came out by running the cured
bench**, not by reading it.

### 17.9-bis ⛔⛔ THE THIRD AND FOURTH OF `07-b64-rete.py` — and the fourth is the biggest

**Third.** `spediti_dal_server` at `None`: `conti_del_server` returns `{"esito": "NIENTE DA LEGGERE"}`,
and `None == 0` is **false** ⇒ the step went straight to the predicate. The predicates that do not look at the
server (`a_pulito`, `a_sorpassi`) gave **green on a round in which the server's end had not been
read at all**. ⇒ Now it is **mute**.

**Fourth — ⛔ and this dirties the numbers, not only the verdicts.**
`[M]` **the closing of a session is slow when the pacer has a queue**: the profile at 10 % loss
took **29 seconds more** than the others to write its «final count» line. ⇒ The
**next** round took its `riga0` **before** that line existed, and `conti_del_server()`
read **the count of the previous round**.

⭐ **The signature is unmistakable**: `[M]` three profiles in a row reported the **very same
numbers** («sent 4999 · refused 3 · resent 7410»), which were the count of the **first** of the three.
The real count of the second was **4 632**. ⇒ The new predicate gave **red on someone else's
denominator** (4 152/4 999 = 0.831), while with the right denominator it was 4 152/4 632 = **0.896**, green.

⚠ **And the same delay produces a second, worse effect**: the next step died with
`CONGEDO 0x0F GIA_ATTIVA_REMOTA` — the previous one's slot was **still occupied**, and it is the
30 s lock of **§17.5**. ⇒ **A round can fail because of the round before**, and the `[audio]
ricevuti 0` that came out of it is **exactly the number the old `a_non_si_apre` would have called
green**. ⭐ The two defects of §17.4-bis and the ghost of §17.5 fed each other.

**The cure**: `registro_posato()` — one waits for the count of «final count» lines to stay **still
for 3 s** before starting a step — and `conti_del_server(riga0, n0)` **demands a line of its own**,
otherwise it stays mute.

**The new round of `07-b64`** `[M]` 23 Aug, port 7801, 25 s per profile: **9 steps · 0 red ·
0 mute**, and the positive control (`--controllo-rosso`) gives red with exit 1 — the verdict can
still fail. ⭐ The step at 10 % confirms the count of the two directions: **4 077/4 504 = 0.905** against
`1-p` = 0.901. **It is `1-p`, not `1-(1-p)²`**: a datagram goes **one direction only**.

### 17.9-ter ⭐ THE THREE CURES OF `09-b70-ritmo.py`, and the number that proves the second

`sudo -S` covering only the first link ⇒ new `catena_root()`, a single `sudo -S bash -c` with the
chain inside. `[M]` the §11.1 reader now **really gets written** (4 130 bytes) and reduces
**794 frames** per round; the old form on the same command gave `Permission denied`.

The `< file` that steals stdin ⇒ `righe_registro()` returns **`None`**, not 0, and the guard sits where the
number **is consumed**. ⭐ **The number that proves the cure:**

| | starting line | `ciclo:` lines | `attese_a_vuoto` |
|---|---|---|---|
| moving round | 327 | 21 | **1 607** |
| still round | 3 711 | 21 | **1 604** |
| ⛔ old form (`riga0` = 0) | 1 | 49 | **4 041** |

⇒ With the defect, the still round would have declared **4 041 instead of 1 604** — **2.5 times**, and
rising at every round. ⛔ And it is precisely the column with which `p_I1` decides **whether to refuse to
judge**.

**And the false premise of I1**: the leg «zero abandons with a still scene» is now **conditioned on the
loss read from the installed `qdisc`**, not assumed to be zero. With loss > 0 the predicate **refuses**
instead of accusing the product (it was the false red of `casa-cattiva`).

**Fourth cure, found by the real round**: the §11.1 reader did not start because `01-b4-validatore.py`
is not among the files that `07-b64-terreno.sh porta` ships ⇒ empty journal ⇒ the bench gave **red on
«does not detach» on a session alive for 797 frames**.

### 17.9-quater ⭐⭐ `09-b76` — THE RIGHT NAME, and the grid redone

`p_niente_stacco` is **split in two**, because they are two facts with two causes:

- **`p_connessione_viva()`** — holds on **all** profiles (§3.3/§8.3, even below the floor) and
  questions the **witnesses of the connection**, not the frames: the client (*«still attached after
  N s»*) and the log (`congedo motivo=`, `posto NEGATO`, ban), **with the reason printed**. ⚠ The third
  possibility — *«it never opened»* — is **mute** by construction, not red.
- **`p_consegna_non_si_ferma()`** — coverage ≥ 0.90 of the seconds that saw at least one
  frame, and ⛔ **no hole ≥ 1.0 s**, **tail included**. ⚠ The 0.90 threshold **is not new**: it is the
  same the old predicate used. **The number does not change: the word changes, and that is the whole
  cure.** The 1 s hole has its reason: §2.1 puts the floor at 25 frames/s, so a
  second at **zero** is off the scale, not «a low rate».
- ⚠ Declared price: `[M]` on the thirteen healthy profiles the maximum hole goes from **0.04 to 0.35 s**,
  against **14.26 s** at `raffica-forte` — more than an order of magnitude of margin, **zero false
  reds**, diagnoses included.

⭐ And `--certifica` now carries the case that had fooled the bench: **the same round gives red on
delivery and green on the connection**. 49 cases out of 49.

**`raffica-forte`, with the right name and the numbers** `[M]` (probe: **11.10 %** loss in 197 bursts,
average 4.51, max 27): **nobody detached** — client attached for all 25 s, zero farewells. What
stops is **delivery alone**: **7 seconds out of 25** saw a frame, **14.26 s of still screen
in a row**, 952 `FOTOGRAMMA NON SPEDITO` lines, `cwnd` median **8 948 B** against **105 616 B**
of the reference (**12 times less**), `cwnd_left` median **0**. ⭐⭐ **And the server says it by itself**:
`⚠ la finestra e' chiusa` on **10 `rete-quic` lines out of 18** — it is the witness of §17.3 giving the
answer without anyone having to deduce it.

### 17.9-quinquies ⛔⛔ AND TWO GRIDS OF THE SAME BENCH DO NOT MATCH — declared, not smoothed over

The `09-b76` round redone tonight **does not reproduce** that of §17.1 on two profiles:

| profile | §17.1 (binary `51b5994`) | new round (binary from HEAD) |
|---|---|---|
| `perdita-0,5` | 40.06 fps · 0 keyframes | ⛔ **19.27** fps · red spiral |
| `jitter-5` | 39.30 fps | **31.45** fps |
| `perdita-1` | 9.56 | 12.32 |
| `raffica-1` | 23.94 | 29.47 |

⛔ **I do not smooth it over, and I do not choose which is good.** The known differences between the two rounds are at least
three — different binary (HEAD carries the `rete-quic` lines, that is **one more `registro_dice` per
second**), machine **rebooted** in between, and the ground rebuilt. ⇒ `[?]` **I do not know which of the
three.**

⭐ **What survives anyway, because it does not depend on the exact point:** the shape is the same in
both rounds — a healthy line at ~40 frames/s, a **cliff** within the first percentage
point of loss, the keyframe spiral as mechanism, and jitter that bites **without losing
a packet**. ⛔ What could **no longer** be said was **where** the step was.
⇒ ⭐ **Untangled by §17.11**, and the answer is more interesting than the question.

### 17.9-sexies ⭐ THE RE-VERIFICATION OF `09-b79` — **no number was dirtied**, and they are three proofs read

`09-b79-cure.py` wrapped `RETE.root` instead of the cured chain. ⚠ And **writing
`B70.root` was not enough**: when b79 arrives, `B70.root` has **already** been replaced by `09-b76:416` with a
wrapping that in turn calls `RETE.root`. ⇒ The chain is rebuilt from the pieces
(`RETE.rem(B70.catena_root(c))`), and if `catena_root` is not there **the bench stops instead of
measuring**.

⛔ But the numbers of §17.6 **hold**, and not on trust:

1. `[R]` **the defect had not yet been cashed in**: at 19:00 `09-b70.root()` still did
   `return RETE.root(...)`; the cure is from **19:41**, after. Wrapping `RETE.root` was then
   *identical*. The defect was **prospective**;
2. `[R]` **the `riga0` was there**: `09-b76` already replaced `righe_registro` with its own, with the redirect
   **inside** `bash -c`. `[M]` And the signature in the data confirms it: on all **36** cells
   `attese_a_vuoto` lies between 1 973 and 2 156 — **constant, not rising** (on `ritardo-30` A/B/C:
   2 015 / 2 006 / 2 016). b70's cumulative was 4 041 against 1 604, **rising**: here it is not there;
3. `[R]` **the count of another round is structurally impossible**: `07-b64-terreno.sh` does
   `: > registro.log` at every `accendi`, and this bench **restarts the server at every arm**.
   `[M]` Counter-proof: no pair of cells carries identical numbers from the log, and three cells
   said «NIENTE DA LEGGERE» instead of the neighbour's number — ⭐ proof that **in the window there was
   nothing to steal**.

⭐⭐ **And the division that counts**: `[R]` the predicates on the spiral, on the rate and on the healthy line
read **only** from the client's §11.1 trace; from the log come only four numbers of
**corroboration**. ⇒ *«the spiral switches off only with arm C: 51.7-88.1 % → 0.0-5.6 %»*
**does not go through the log**, and the five red profiles are not redone.

**Remeasured `ritardo-30` with three arms** — the predicate worth more than all the others:

| arm | fps | keyframes | final drift | max drift |
|---|---|---|---|---|
| A | 39.94 | 0.0 % | 0.0 ms | 10.1 ms |
| B | 39.94 | 0.0 % | 0.2 ms | 11.0 ms |
| C | 39.32 | 0.0 % | −0.1 ms | 6.2 ms |

**S′ green**, and it holds the comparison with 19:00 (39.85 / 40.19 / 39.63). ⭐ And the spiral lines
of arm A come back **identical** (`chiave_aspetta` 1, `delta_non_spedito` 5,
`abbandonato_in_coda` 1): **a cumulative number does not reproduce, these do.**

## 17.11 ⭐⭐⭐ WHERE THE CLIFF IS — *23 Aug, dead of night*: **the step is DOUBLE**, and the product is **bistable**

`banchi/09-b80-dirupo.py` · **42 rounds** · loss **read** by a probe of **20 000 packets** at
every cell (⛔ at 0.1 % eight packets do not measure a tenth of a point) · denominator run at
**opening and closing** (39.95 → 39.93, **0.1 %**: the machine has not drifted) · machine stilled
by name before starting · cures off for all 42 rounds.

### 17.11-bis ⛔ First the yardstick, then the measurement — and the yardstick is coarse

⛔ **It makes no sense to compare two rounds if one does not know how much the noise between two identical rounds is worth.**

| profile | rounds | spread | half-spread |
|---|---|---|---|
| loss **0.00 %** | 3 | 39.89-40.17 | **0.4 %** |
| loss **0.50 %** | 3 | 28.16-36.70 | **14.8 %** |
| loss **0.50 %** | 5 | 20.79-36.70 | **27.6 %** |
| loss **0.75 %** | — | — | **46.6 %** |

⇒ The contradiction of §17.9-quinquies is worth **35.0 %**: the noise **does not explain all of it, but
covers four fifths of it**.

⭐⭐ **And the real fact is here**: the dispersion **grows with loss** (0.2 → 8.5 → 23.8 → 46.6 %)
and **not with load**. `[M]` CPU was **3.7-4.7 %** in *each* of the 42 rounds, load 0.3-0.8
on 20 cores. ⇒ The «loaded machine» hypothesis is **ruled out**, and what remains belongs to the product:

> ⛔⛔ **near the edge the spiral is BISTABLE.** `[M]` at **0.20 %** loss, same binary,
> same ground, twenty minutes apart: **`0 chiavi · 40,16/s`** and **`24 chiavi · 33,84/s`**.

⇒ It is not a threshold: it is a **bifurcation point**. The same input gives two outputs, and which of the
two depends on how the first handful of seconds went.

> ⛔⭐⭐ **«BISTABLE» IS THE WRONG WORD, and the correction is in §21.2** — *24 Aug*. They are not two
> branches between which the product chooses: it is **a one-way trigger**, with a **constant** probability
> every second. The 25 s rounds were not a coin tossed on the product: they were **a coin
> tossed on how long we had watched**.

### 17.11-ter ⭐⭐⭐ THE STEP IS DOUBLE, and the two halves are very far apart

| | where it falls | what it is |
|---|---|---|
| **the MECHANISM** — the keyframe spiral (§3.3) | ⛔ between **0.00 % and 0.10 %** of real loss, **on both binaries** | that is **at the first lost packet** |
| **the SYMPTOM** — below the floor of 25/s (§2.1) | between **0.53 % and 0.75 %** (HEAD) · between **0.27 % and 0.47 %** (`51b5994`) | that is **five times further on** |

⛔⛔ **This is the discovery, and it changes the way of reading the whole of §17.1**: the defect **does not begin
where it is seen**. Between the first lost packet and the moment the user notices there is half a
percentage point of loss in which **the product is already degenerating into keyframes** — and the degradation
is already *in space and in time together*, which §3.3 forbids — **while the frames per second still
say everything is fine**.

⇒ ⭐ **A bench that had looked only at frames/s would have given green up to 0.5 %.** The
column that sounds the alarm five times earlier is **the keyframe share**, and it is the reason why §17.1
carries it beside frames/s instead of in their place.

**The fine grid (HEAD)** `[M]`:

| real loss | fps | keyframes | worst second |
|---|---|---|---|
| 0.000 % | 39.95 | **0** | 37.5 |
| 0.100 % | 39.44 | 2.5 | 23.5 |
| 0.195 % | 37.00 | 12 | 21 |
| 0.253 % | 34.83 | 20.5 | 5 |
| 0.532 % | 27.29 | 48 | 4 |
| **0.748 %** | ⛔ **13.50** | 101.5 | 4 |
| 0.998 % | 7.23 | 119.5 | 3.5 |
| 1.475 % | 5.52 | 112.5 | 3 |

⭐ **And nothing ever detached, and delivery never stopped** — coverage 1.00 and maximum hole
≤ 0.37 s **everywhere**, not even at 1.5 %. ⇒ The prohibition of §3.3 holds; what gives way is the ladder, not the wire.

### 17.11-quater ⛔ The range of the first round is withdrawn, and the binary has nothing to do with it

**The «0.36-0.94 %» range of §17.1-bis is wrong** and §17.11 withdraws it. It came from a
`perdita-0,5` that had given *40.06 frames/s with **zero** keyframes*. `[M]` **In 7 rounds at ~0.5 % of
real loss, on both binaries, the keyframes were 11, 47, 44, 72, 24, 112, 129 — never zero.**
⇒ That number **does not reproduce**: it was the lucky branch of the bistability, taken once and
mistaken for the rule.

**The binary** — `HEAD` (`2954bf0`) md5 `dae98670…` against `51b5994` md5 `760c6fd7…`, and between the two
`src/` changes in **a single commit** (+412 lines, 0 removed):
- ⛔ **on the clean line it does not count**: 39.95 against 39.25 = **1.8 %**, within the yardstick.
  ⇒ `[M]` **the suspicion «the `rete-quic` line costs» is REFUTED**: one more `registro_dice` per
  second cannot be measured;
- it counts **only where there is loss**, and ⭐ **they cross**: HEAD yields more below 0.5 % (37.0 against
  29.1 at 0.2 %), less above 0.75 %. ⚠ **But the reds above 0.75 % rest on cells whose
  internal dispersion (46.6 %) exceeds the yardstick**: they are **clues, not numbers**. Those at 0.2/0.3/0.5 %
  are solid and all say the same thing;
- ⭐ and `51b5994` is **already inside the spiral at every cell** (55-142 keyframes): that is why it is *stable* —
  **it has no edge to oscillate on**.

## 17.10 What remains open after this section

1. ⭐ **the cures against the spiral are MEASURED** (§17.6) and stay **off**: I6 keeps them behind
   the switch until the user has looked at them. ⇒ ❓ **the user's decision**, and he has the two
   numbers he needs — the rate gained (1.7-2.8 times) and the delay paid (−38/+161 ms on the
   ordinary profiles, 4.5 s on `raffica-forte`);
2. ⛔ **the 36 % of audio refused by ngtcp2** on `casa-cattiva` (§17.2-quater): the same congestion
   window that in video produces the spiral, and it is not a defect of the reorder cure;
3. ⭐ **`raffica-forte` is explained** (§17.1-quater): nobody detaches, delivery stops —
   `cwnd` at ~10 KB and 860 frames never sent. ⛔ It remains serious (still screen) and **the cures
   cure it**, but the name was wrong and the predicate is being cured;
4. ❓ **the ghost of §17.5**: the user's decision, not a measurement's;
5. ⭐ **the cures to the benches are applied and the benches run again** (§17.9): nine defects in all,
   ⛔ **all of the form «silence instead of red»**;
5-bis. ⭐ **the contradiction between the two grids is untangled** (§17.11): it was not two binaries, it was the
   product that **near the edge is bistable**. ⛔ And the most important fact of the
   section came out of it: **the step is double** — the mechanism starts at the **first lost packet**, the symptom
   is seen **five times further on**;
5-ter. ⏳ **and the bistability has no explanation**: `[?]` why the same input gives
   `0 chiavi · 40,16/s` or `24 chiavi · 33,84/s` has not been investigated. It is the first thing to
   look at if one wants to cure the defect **where it begins** instead of where it is seen;
6. ⚠ **reordering on streams remains without a direct witness** (§17.3): `dgram_falsi` holds
   for audio only.

---

# §18 · ⭐⭐⭐ THE TWO CURES DECIDED BY THE DIRECTOR — *23-24 Aug 2026, night*

> *«Ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps. Se in 10 secondi non
> arrivano più pacchetti è chiaro che la connessione è morta. […] se all'interno di un intervallo di
> 1-2 secondi c'è una perdita di pacchetti piuttosto copiosa direi di trattarla come il caso in cui
> la connessione è caduta.»*
> — ⇒ `DECISIONI.md` **§3.1-quater**, **§3.1-quinquies**, **§3.1-sexies**.

⛔ **Where it comes from**: the choice between **two measured evils** (§17.1, §17.6). With heavy burst
loss, **without** the cures the screen freezes for **14.26 s**; **with** the cures it moves but with
**4.5 s of delay**. ⇒ The user decided that **neither of the two should be served**: such a line is not
slow, it is **broken**. And to the question of what he sees, he chose among three: ✅ **the wire drops and one
re-enters by hand** — not an automatic reattach, not an invisible restore.

⚠ **The objection was raised and overcome**: *«on a bad network the diagnosis "the line dropped" is
frequent, and making it cost a manual login makes the product unusable precisely where it is needed»*.
⇒ From there comes the prerequisite: **§18.3, the ghost**.

## 18.1 ⛔⛔⛔ THE FIRST QUANTITY WAS WRONG — and the bench refuted it before it shipped

The cure was written on ngtcp2's `pkt_lost / pkt_sent` within a window: a loss fraction,
threshold **50‰ (5.0 %)**, tuned with two apparently comfortable margins — 2.9× above the worst that
holds (`casa-cattiva`, 1.71 %) and 2.2× below the one that serves nobody (`raffica-forte`, 11.10 %).

⛔ **`banchi/09-b81-linea-morta.py` killed it in ten minutes** `[M]`:

| profile | loss **injected** (probe) | loss **DECLARED** by ngtcp2 | the line |
|---|---|---|---|
| `casa-cattiva` | 1.86-2.15 % | ⛔ **512‰** (51.2 %) | **HOLDS for 10 minutes** — 9.60 frames/s, coverage 1.00, max hole 0.50 s, client attached at 599.99 s |
| `raffica-forte` | 12.28-14.00 % | **123‰** (12.3 %) | **does not hold** — coverage 0.20, hole 30.06 s |

⛔⛔ **The quantity orders the two cases BACKWARDS**: the line that **works** declares **four
times more loss** than the one that does not work. ⇒ **No threshold separates them** — any value that
lets `casa-cattiva` through (≥ 512‰) also lets `raffica-forte` through; any value that stops
`raffica-forte` (≤ 123‰) stops `casa-cattiva` **first**. **It was not a tuning to redo: it was the
wrong quantity.**

⭐⭐ **And the cause is the central fact of this phase, come back to bite us.** `casa-cattiva` carries
`delay 40ms 20ms distribution normal`, and the probe measures there **93.5 % of packets out of order**
with 1.9 % of real loss. **ngtcp2 counts an overtaken packet as lost.** ⇒ `pkt_lost` on
a line that reorders **measures the reordering**, not the loss — and it is §3.1-ter presenting us with the
bill: *we had written that disorder is mistaken for loss, and then we built
a decision on top of it*.

⚠ And it was not the start of the connection: with the first ten windows removed, **399 out of 399** stay above
threshold, median **524‰**, uninterrupted for ten minutes.

⭐ **The falsifier had been declared `[?]` by whoever wrote the cure**, before the bench
ran: *«the threshold is on the **declared** fraction, while the two extremes are the **injected**
loss — with jitter and reordering the declared one can be higher»*. ⇒ It served: the bench
knew **what to go and break**, and broke it at the first round.

## 18.2 ⭐⭐⭐ THE RIGHT QUANTITY — **the output stall**

⭐ **The data pointed to it by themselves**: `casa-cattiva` maximum hole **0.50 s**, `raffica-forte`
**30.06 s** — **sixty times**. ⇒ What separates the two cases is not **how much is lost**: it is **whether the
frames get out**.

> **the quantity is: how long a frame has not gone out despite there being some to send**

Two **local and monotonic** counters (form P8→P20 of `RCP.md`: an observable fact, never a
clock) plus an instant:

| | how it is computed |
|---|---|
| **«it went out»** | the **video bytes delivered to ngtcp2** in `coda_consegna()` — the only point where the bytes are really inside a packet |
| **«I had something to send»** | video queue not empty **or** `lm_offerti` risen (in `video_a_una()`, **before** brake, clearing and refusal) |

⛔⭐ **The second term is not an extra, and it is the line that makes the cure honest**: without
`lm_offerti`, **the rate regulator would hide the stall** — it stops producing,
`video_sgombra()` abandons the deltas, the queue empties, and *«I have nothing to send»* becomes true
**while the screen is still**. The cure would acquit itself precisely in the case it must catch.

⛔ **And if there is nothing to send the count does not even start**: `[M]` in this phase the still scene
delivers **1 frame in 30 s and then zero** — and it is not a defect, it is Mutter's `RecordVirtual` that
delivers only on change (§13, the wake-up costs 13 ms). ⇒ A cure that started there
**would throw out whoever watches a still desktop**, which is the worst way it could fail.

⚠ **Bytes are counted, not whole frames**, and the reason is declared: a keyframe of ~60 000
bytes on a narrow line can take seconds to get out completely, and in frames those seconds would be a
«stall» **while the wire is working**. A byte that leaves is a wire that carries.

### 18.2-bis The threshold — **5 000 ms**, and the two margins with the intermediate case

| | longest stall/hole | |
|---|---|---|
| thirteen healthy profiles | 0.04-0.35 s | they hold |
| `casa-cattiva` | **0.50 s** | ⛔ **HOLDS — it must not be declared dead** |
| ⚠ `raffica-1` | **a whole second at zero** | but it delivers **23.94 frames/s**: it holds very well |
| `raffica-forte` | **14.26 s** (30.06 in the other round) | does not hold |

⇒ interval **1.00-14.26 s**, geometric centre **3.78 s**, choice **5.0 s** — ⭐ **above** the
centre, on purpose. Margin **5.0×** above the worst that holds, **2.9×** below the one that serves no purpose.

⛔ **The narrow side uses the SHORTER of the two stalls of `raffica-forte`**, not the longer: a
margin written on the lucky number is not a margin.
⛔ **And the asymmetry is deliberate**: the two errors **do not cost the same**. Erring high = a few
more seconds of still screen. Erring low = **throwing out someone who was working**, and
it cannot be remedied.
⚠ **Even the sampling errs on the good side**: the count restarts from the instant of the round
(≤ 1/s), not from when the bytes really left ⇒ the measured `stallo_ms` can be up to ~1 s
**shorter** than the true one. It fires later, never earlier.

### 18.2-ter ⭐⭐ THE PROOF — *24 Aug 2026*, and the margin is **measured**, not «it did not fire»

⛔ The line comes out **only when it fires**. ⇒ A «it did not fire» does not say **how close it came**: the
bench replays the same profile **with ever lower thresholds** until one fires, and then the
product prints its `stallo_ms`.

| profile | maximum stall | margin on the 5 000 ms threshold | hole at the client |
|---|---|---|---|
| `ritardo-30` (healthy) | < 500 ms | **> 10×** | 0.157-0.175 s |
| ⭐ `casa-cattiva` | < 500 ms | **> 10×** | 0.359-0.479 s |
| ⚠ `raffica-1` | **1 001 ms** | **5.0×** | 0.52-3.73 s |
| ⛔ **still** scene | *the count does not start* | — | 1 and 3 frames in 90 s |

⭐ **`raffica-1` confirms the derivation with an independent number**: the narrow side is worth
**1.00 s**, exactly the one of the box, and the margin is the declared **5.0×**.

**`casa-cattiva`, ten minutes, cure on: ZERO FIRINGS** — 9.71 frames/s, coverage **1.00**
(600 s out of 600), maximum hole **0.479 s**, client attached at 599.88 s, no farewell.

⭐⭐ **And the comparison that closes the refutation**, in the **same** round: the **witness** says `permille`
median **529‰**, with **392 windows out of 392** above the old 50‰. ⇒ **The old cure would have killed
this very session; the new one does not touch it.** Same profile, same bench, same ten
minutes: **only the quantity on which one decides** changes. And on the other side `raffica-forte` — the one
that does *not* hold — declares `permille=133`, that is **less**.

**The real firing** `[M]`: `raffica-forte` (13.19 % injected) fires at **18.95 s**, with
`causa=stallo stallo_ms=5008 · offerti=198 · usciti_byte=0 · coda_video=31146` — ⭐ **both halves
true**: we had something to send, and nothing went out. And the wire drops.

**The silence** `[M]`: `kill -9` ⇒ `silenzio_ms=10006`, `prove=12`, **10.24 s** after the shot, and
in the same line `stallo_ms=8 offerti=0` — ⭐ **the two causes stay separate**. With the cure off,
zero firings.

**The still scene** `[M]`: 90 s of a desktop that does not change, zero firings at the threshold in force **and at
1 000 ms**, that is five times narrower. ⭐ And the scene was **really** still, **verified and not
hoped**: the server's count says 1 and 3 frames in 90 s, all sent.

**The defaults (I6)** `[M]`: without `--linea-morta`, zero firings and zero evictions, and the two profiles
sit in the grid of §17.

⚠ **One thing to say, and it goes in the prudent direction**: the **stall** (server: bytes out) and the **hole**
(client: frames arrived) **are not the same quantity**, and the threshold is derived from the second
while the cure measures the first. `[M]` on `raffica-1` one round gave a hole of **3.73 s** with the stall
not firing even at 1 000 ms: **the bytes leave, what is missing is the retransmission**. ⇒ The error
goes on the good side, but the number of the derivation is **prudent, not exact**.

### 18.2-quater ⛔ What became of the `permille` — from **judge** to **witness**

`--linea-morta-permille` is **removed**: an option that accepts a number **without using it** is worse than
an option that does not exist, because whoever types it believes they have tuned something. ⇒ Now it gets help and
exit 2.
⭐ But `permille=` **stays in the line as a witness**: it is the best measure of **reordering** the
server has **on the streams**, where `dgram_falsi` (§17.3) does not reach. ⚠ And the bench verifies
the **absence** of the option **by typing it**, not with a `grep`: `[M]` the string in the binary is there
all right — it sits in the help text — and the first round of that check **gave red on a
right binary**.

## 18.3 ⭐⭐ THE EVICTION OF THE GHOST — and lowering `SILENZIO` was discarded **on a measurement**

⛔ The obvious road — bringing `SILENZIO` from 30 s to 10 — **breaks**, `[M]` 16 Aug: between two
authenticated packets of a **still but ALIVE browser** pass **15 004 / 15 005 / 15 002 ms**. It is the
browser's keep-alive, not ours. ⇒ At 10 s **every client that watches and does not touch loses its slot at
every keep-alive round** — it is the regression already paid for on 16 Aug (*«una seconda scheda è entrata
e ha preso il desktop del primo»*).

⚠ **And `SILENZIO` governs four more**: the warning at `SILENZIO/2` (it would go from «never on a
healthy session» to «on all of them»), the release of pressed keys (⛔ a `Ctrl` held down during a
network pause of 12 s would be released **under the fingers**), the order silence→inactivity, and **three
documents** that declare the number to the user.

⇒ **The road chosen is narrower and more targeted**: `--sfratto-ms N` (**0 = off**, default;
recommended **15 000**). It fires **only when someone asks for that slot**, never by itself, and **only between
clients of the same user**.

⛔ **§8.2 is not violated, it is applied**: *«no client attached and **alive** is ever ousted»* —
the occupant here is attached but **not alive**, and until now the only clock that distinguished them was the
30 s one. ⭐ `torna_a_parlare()` restarts **only from `S_STACCATA`**: that is why the eviction changes the
**state** and does not merely remove the slot, or the ghost would stay `S_ATTIVA` without a slot.

`[M]` **The ghost drops by 48 %**: from **32.13 s and 14 refusals** to **16.83 s and 7 refusals**. ⭐ And with
the dead line on it drops to **~10 s with zero refusals** — the slot becomes free at the first attempt.

**Two different users** `[M]`: zero evictions, the second user enters on **their own** slot with zero
refusals. ⚠ The line `⛔ SFRATTO NEGATO` **does not come out**, and it was predicted `[R]` before running: the
register of slots is indexed by name, so `POSTO_OCCUPATO` already implies «same user» and that
branch is not reachable. **The protection is done by the structure; the explicit check stays as a
net** — the day `MAX_ATTACCATE` becomes the table of a multi-tenant server it would be
the only thing to hold.

## 18.4 ⛔ AND THE SENTENCE THAT LIED

*«That user is already connected from another device»* (`src/pagina.html`, `MOTIVO[0x0F]`) is a
**diagnosis the server is not able to make**: it does not know whether the other client is another device or
is the same user who has just dropped. ⇒ Now it says **what it knows** and gives the gesture:

> *«this session's place appears to be occupied by another client — if it was you and you have just dropped,
> try again in a few seconds»*

⚠ **And it counts more than before**: after §3.1-quater **one re-enters by hand**, so it is the **first sentence the
user meets when re-entering**.

## 18.5 ⚠ And a price declared for a case that does not exist — corrected

PINGs go at half the threshold when the cure is on, and the cost had been declared at
**0.21 kbit/s** per session. ⛔ The bench **could not isolate it, and refused to give an empty
green**: `[M]` a «still» session costs anyway **2 463 kbit/s** of PCM audio (§4.3, which does not
switch off — a `CIAO` without a common audio codec gets `0x09 NIENTE_IN_COMUNE`), that is **11 727 times**
that number; the difference on−off is **+0.539 kbit/s**, within the noise.

⭐ **And the real fact**: `[M]` on a live session the counter **never stops for 0.6 s** ⇒ the
keep-alive **never has a chance to fire**, and those 0.21 kbit/s described **a case the
product does not enter**. A price declared for a case that does not exist **is worse than no price**.

## 18.6 What remains, after §18

1. ⭐ **the two cures are tested and stay OFF** (I6): `--linea-morta` and `--sfratto-ms`.
   ❓ **The decision to switch them on is the user's**, and now he has the numbers;
2. ⏳ **the cures against the spiral** (§17.6) stay off and wait for **his eyes**, which is the only
   thing that cannot be delegated to a measurement;
3. ⏳ **the bistability** of §17.11 has no explanation yet;
4. ⛔ **the 36 % of audio refused by ngtcp2** on `casa-cattiva` (§17.2-quater) has no cure yet;
5. ⚠ **the stall and the hole are not the same quantity** (§18.2-ter): the derivation is prudent, not
   exact, and a round that measured them **together** would make it exact.

---

# §19 · ⭐⭐⭐ THE USER'S JUDGEMENT ON THE REAL PATH — *24 Aug 2026, morning*

⛔ **It is the section that counts more than all the others**, and for the reason written at the top of the document: in
v1 the homologous phase was validated with PSNR, SSIM and the developer's eye, and the
user's judgement on the real desktop was *«siamo tornati indietro»*. **The phase was reset to zero.**

**The bench**: the user's real session, browser on the **laptop** (192.168.0.3, WiFi `wlo1`), server
on the test machine, port **7920**, binary `2792271f…` from the working tree, canvas
**2544×926**, ⛔ **all cures off**, glibc trap **off** (the server runs at real
speed).

⭐ **And the network was dirtied on the CLIENT side**, not the server's: video arrives **incoming**
on `wlo1`, so the fault sits on an `ifb0` with `netem`, fed by a `u32` filter on **only
incoming UDP port 7920**. ⛔ On the test machine the same traffic would pass through `enp7s0`,
where ssh passes, and that one is not touched. ssh is TCP on 22 and is not filtered.
⚠ And the fault **disarms itself** after N seconds, with a detached guardian: the same discipline
already used on `lo`.

## 19.1 ⭐⭐⭐ THE LADDER, AND IT COMES FROM HIS EYES

| loss **measured on the wire** | his judgement |
|---|---|
| 1 % | *«mi sembra ok»* |
| **5.6 %** | *«è tutto fluido»* |
| ⛔ **10 %** | *«adesso si è bloccato»* |

> ⇒ **The border of real use lies between 5 and 10 per cent loss.**

⛔⛔ **And this CONTRADICTS the bench, by an order of magnitude.** §17.11 puts the cliff inside the
first percentage point: the keyframe spiral starts at **0.10 %** and the rate falls below the
floor at **0.53-0.75 %**. `[M]` On the real path, at **5.6 %** — that is from **seven to
fifty-six times** more loss — the user does not notice.

## 19.2 ⛔ AND THE TEST WAS REDONE TWICE, BECAUSE THE FIRST DID NOT BITE

⚠ **It must be written because it is an error of method of mine, and it is the third of the same family** (after the
video full of grain of §16.4 and the nine «expected» never compared of R13): a judgement on a test that
does not stress is not a judgement.

`[M]` **First round, and it did not count**: loss at 1 % on and verified (the server saw it:
*«the line is losing»*, 27 packets declared lost, 22 audio datagrams lost), **zero frames
abandoned out of 920**, **two keyframes in all**. ⇒ No spiral — but the reason was in the number I
was not looking at: ⛔ **his frames weighed 242-283 bytes.** Two hundred bytes. The bench collapsed
on a scene that filled the wire with 3 Mbit/s; here the loss **had nothing to break**.

`[M]` **Second attempt, dragging a window**: frames up to **3 801 bytes**,
**zero keyframes** out of 400, **2 abandons out of 2 181**. ⇒ Still not enough: the bench worked on
frames **seven times larger**.

`[M]` **And at 5 % the first judgement was WITHDRAWN before writing it**, by counting the packets
that really went through the fault: **221, with 18 thrown away**. ⛔ Eighteen packets are not a test.
⇒ Redone with **thirty seconds without ever stopping**, and then yes: **7 596 packets in the fault, 423
thrown away = 5.6 % real**.

⭐ **The number that makes the good round valid** — and that the two previous ones lacked: frames up to
**77 304 bytes**, that is ⭐ **three times larger than those on which the bench collapsed**. With those:
**keyframes 3.8 %** (23 out of 600), **abandons 11 out of 3 017** (0.36 %), and the judgement *«è tutto fluido»*.

⛔ **The lesson, and it holds beyond this phase**: the step is not decided by the loss, it is decided by **how much
the scene asks**. The bench produces a stress that demands **forty frames per second
of continuous change**; a real desktop — even while dragging a window — changes **in
jerks**. ⇒ **It is not the same stress**, and the bench's predictions **do not apply to the
product as it is used**.

## 19.3 ⭐⭐ THE FREEZE AT 10 %, CAUGHT IN THE INSTANT — and the mechanism is the one of §17.1-ter

`[M]` At the moment the user said *«si è bloccato»*, the server's log said:

| | |
|---|---|
| **`cwnd = 2 888 byte`** | ⛔ the congestion window **collapsed to two packets** — ten times less than the minute before |
| `cwnd_left = 2 888` · **in flight = 0** | ⛔⭐ **it is not that the wire is full: there is NOTHING in flight.** The server *could* send, and does not |
| **27 `NON SPEDITO` frames** | and the delivered counter **stuck at 3 117** over three readings in a row |
| keyframes | risen from 4 to **16** |
| `persi=664` · `dgram_persi=493` | `giudizio=⛔ la linea perde` |

⇒ ⭐ **It is exactly the chain of §17.1-ter, seen on the real path**: the window closes → the
frames do not leave → keyframes are requested → the screen stops. The bench's mechanism **is
right**; what was wrong was **where** it placed it.

⭐⭐ **And `cwnd_left = cwnd` with «in flight = 0» is the signature that acquits the wire and accuses us**: it is not
observed congestion, it is the pacer refusing. It is the same picture as `raffica-forte` (§17.9-quater,
`cwnd` median 8 948 B, `cwnd_left` median 0) on a real line.

## 19.4 ⚠ AND TWO THINGS THIS SESSION COULD NOT TEST

1. ⛔⛔ ~~**The applications the coordinator launches do not reach the user's screen.**~~
   → **WRONG, and the correction is in §20.1.** `[M]` `mpv` **does arrive** — 241 frames in 8 s
   on a controlled bench. When I judged it *«does not arrive»* ⛔ **there was no client
   attached**: the server was not sending, and the counter was stuck **by construction**. The «167 bytes»
   were the last values from before.
   ⚠ **I judged with a yardstick that in that scene could say nothing**, and it is the same wound
   as §19.2 — the third time in two days. **Firefox** instead is really broken, but `[M]` **also
   outside REMOTIX**: it is not ours (§20.1).
2. ⭐ **The cures were tested by eye** ⇒ **§19.6**, and the verdict is that **they do what they
   promised and it is not enough**.

## 19.6 ⭐⭐⭐ THE CURES, LOOKED AT — **they do what they promised, and it is not enough**

`[M]` 24 Aug, same session, same binary, **same 10 % loss**, and changing **only
the server's switches** — verified from the startup lines, not from the command line: queue
threshold **100 ms**, rate regulator **ON**, ⛔ **dead line and eviction OFF on
purpose** (if the wire dropped one would not know whether it was thanks to or because of the cures).

Loss **measured on the wire**: 8 597 packets passed, **905 thrown away = 10.5 %**.

| | **without** cures | **with** the cures |
|---|---|---|
| frames delivered | ⛔ **stuck** — same number over three readings in a row | ⭐ **they continue**: 1533 → 1552 → 1557 |
| frames never sent | **27**, in one burst | ⭐ **1** |
| `cwnd` | 2 888 B | 3 652 B |
| keyframes | 16 | 17 |
| **the user's judgement** | *«si è bloccato»* | ⛔ *«si è bloccato»* |

⭐ **The cures do exactly what the bench promised**: without them, delivery **stops**; with them,
it goes on at **five to twenty frames per second**, and the frames never sent go from 27 to **1**.
The mechanism is cured.

⛔⛔ **And it is not enough.** For whoever watches, five frames per second with that delay **are a freeze
all the same**. ⇒ The number improves and **the experience does not**, and it is precisely the distinction this
phase existed to protect (v1: *«siamo tornati indietro»* on numbers that had improved).

⭐⭐⭐ **And this is the strongest argument in favour of §3.1-quater**, the decision taken by the user
the night before **without having this number**: at 10 % loss **a good version does not exist** —
either the screen stops, or it moves in a way the user calls **frozen anyway**. ⇒ *«Nessuno
dei due va servito»* was not a preference: it was the right reading, and now it has the proof.

**The complete ladder, all from his eyes:**

| real loss | **without** cures | **with** cures |
|---|---|---|
| 1 % | *«mi sembra ok»* | — |
| 5.6 % | *«è tutto fluido»* | — |
| **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |

### 19.6-bis ⚠ AND TWO THINGS SEEN IN PASSING, which were not in the programme

1. ⭐ **The sixty-minute rule fired on a real session, and it is the first time.**
   `[M]` *«prova2 has not touched anything for 3 600 012 ms (cap 3 600 000) — I CLOSE the graphical session»*
   (`DECISIONI.md` §4.8). It asked for the logout politely and, **after ten seconds**, closed it by
   force (`Logout 1` → `Logout 2`). ⚠ And it produced a false alarm: the user saw the screen
   still and said *«il server è ancora bloccato»* — ⛔ **it was not**: `NRestarts=0`, up for
   an hour and a half, and the only core present was from **yesterday**.
2. ⛔⭐ **«Live and mute session» is indistinguishable from «dead program», and the user proved it
   in person** — twice, saying *«si è bloccato»* and *«il server è ancora bloccato»* of a
   server that was perfectly fine. ⇒ It is the same fact as §17.1-quater and §17.9-quater seen **from the other
   side**: there the bench called «detach» a stopped delivery, here the user calls «server frozen»
   the same thing. ⭐ **And it is the reason why the dead line cure is needed**: not because it
   improves the image — it cannot — but because **it tells the truth** instead of leaving a still screen
   that looks like a fault of the program.
   ⚠ And the session **recovers by itself**: `[M]` with the loss removed, `cwnd` climbs back from 2 888 to
   **46 412 bytes** (sixteen times) without anybody touching anything.

## 19.5 ⭐ What this section changes in the decisions

1. ⭐⭐ **The cures are needed, but not for the user's daily work.** `[M]` Up to 5.6 %
   loss the product **as it is** is judged smooth. ⇒ The cures are needed for the **burst case** and for
   **whoever watches video**, not for whoever works. ⚠ It is a good reason to switch them on **calmly**, and not in a
   rush — and I6 stays respected at no cost;
1-bis. ⛔ **And at 10 % they do not save the experience** (§19.6): they cure the mechanism — delivery that continues
   instead of stopping, frames never sent from 27 to 1 — but the user's judgement **does not change**.
   ⇒ Above a certain loss **the degradation ladder has nothing more to offer**, and the only
   honest answer is §3.1-quater: declare the line dead;
2. ⛔ **The bandwidth floor (§3.1-sexies, 30 Mbit/s) has nothing to do with all this.** `[M]`
   In the good round the large frames reached 77 KB and the line was never saturated: what
   closed was the **congestion window**, not the bandwidth. ⇒ ⭐ **§3.1-ter receives its strongest
   confirmation**: bandwidth is a premise, the quantity that decides is the **quality** of the wire;
3. ⚠ **and the bench thresholds must be read for what they are**: `[M]` measurements on a stress
   **ten times harsher** than real use. They are not wrong — they are a **worst case**, and it must be
   written beside every number of §17 that someone might take for a promise.

---

# §20 · ⭐⭐⭐ THE OPEN POINTS, CLOSED — *24 Aug 2026*

⛔ **And two of the four demolished a premise this document took for granted.** The correction is
written, not smoothed over.

## 20.1 ⛔⛔ «APPLICATIONS DO NOT REACH THE SCREEN» — **it was false, and it was mine**

`banchi/09-b82-mostra.sh` · binary `b86cf6df…` from the working tree.

⭐ **`mpv` does arrive.** `[M]` With **only** `XDG_RUNTIME_DIR` + `WAYLAND_DISPLAY`: **241
frames in 8 s, 38 513 bytes on average**. With `systemd-run --user` (the menu's route): **317**. And
`WAYLAND_DISPLAY` **was already there** in the user manager's environment — GNOME writes it there.

⇒ ⛔ **The real cause of this morning's case: nobody was watching.** `[M]` The 7920 log,
minute by minute:

```
08:33   765 fotogrammi ·  49 battiti rete-quic
08:34   708 fotogrammi ·  59 battiti
08:35   228 fotogrammi ·  60 battiti
08:36    13 fotogrammi ·  31 battiti   ← il cliente se ne va
poi     NIENTE, solo «il legame regge» ogni minuto
```

Without an attached client the server **does not send**, the counter is stuck **by construction**, and the
«167 bytes» were the last values from before. ⚠ **I judged in a scene in which the yardstick could
say nothing** — the third time in two days (§19.2, §16.4).

**The three hypotheses I had written all fell** `[M]`: a single compositor and a single
`wayland-0` (⚠ the date of 23 Aug I had read was that of `bus`, not of the socket); **a single
monitor**, `Meta-0` «Virtual remote monitor» 2544×926 scale 1.000; the environment was **not**
incomplete.

### 20.1-bis ⛔ AND THE YARDSTICK WAS WRONG TOO — bytes do not say what I believed

`[M]` Calibration on 8 s windows:

| scene | frames | average bytes |
|---|---|---|
| still desktop | 0-1 | 238-283 |
| ⛔ a **full-screen flag** | **321** | **268** |
| `film-grana.webm` | 226 | 18 600 |
| `duro.mp4` | 240 | 37 081 |

⇒ **A live full-screen window can produce 268-byte frames, that is as much as a still
desktop.** ⭐ **The verdict is the COUNT, not the bytes**: bytes say *how much* changes, the count says *whether*
it changes. ⚠ And in §19.2 I had used bytes as the yardstick: that reasoning holds on the merits (his
frames *were* small) but the right yardstick was another one.

### 20.1-ter ⛔⛔⛔ ~~Firefox is broken — and it is not ours~~ → **REFUTED on 25 Aug 2026**

> ## ⛔⛔⛔ THIS SECTION IS WRONG, AND THE PROOF THAT CLOSED IT WAS FLAWED
>
> *Refuted in phase 10, `fasi/10-multi-tenant-e-il-budget.md` §5.10.* ⭐ **Firefox was never
> broken on this machine.**
>
> ⛔ **The real cause**: `~/.cache` is a **link to `/tmp`** (from `/etc/skel`, base image of
> 30 Jul). Firefox keeps the *local* profile under `$HOME/.cache/mozilla` = **`/tmp/mozilla`**, and
> `[M]` **`/tmp/mozilla` belongs to `prova2`, mode `0700`, created on 23 Aug at 08:03** — that is
> **before** all the measurements of this section. ⇒ For every other user the profile **is not born**.
>
> ### ⛔⛔ And the defect of METHOD is in the «check that closes the question»
>
> It said: *«`firefox --headless --screenshot` as **`nicfio`** — no REMOTIX session, no
> Wayland, no monitor — **hangs the same way**»*.
>
> ⇒ ⛔ **But `nicfio` has the SAME `~/.cache -> /tmp`**, and therefore the same `/tmp/mozilla` as
> `prova2`. `[M]` Verified on 25 Aug: `lrwxrwxrwx nicfio -> /tmp`, and inside
> `drwx------ prova2 prova2`.
>
> ⭐⭐ **The check SHARED the factor it should have excluded** — and such a check does not
> check anything: it shows the same fault for the same reason, and whoever reads it concludes *«then
> it is not the session»* when instead **the session had never been under test**.
>
> ### ⭐ The remeasurement, with only one thing changed
>
> `nicfio`'s `~/.cache` remade as a **real folder**, and **nothing else** — same command, same
> machine, same Firefox:
>
> | | phase 9, 24 Aug | ⭐ 25 Aug, after |
> |---|---|---|
> | `firefox --headless --screenshot` as `nicfio` | ⛔ **hangs**, killed at **60 s**, empty profile | ⭐ **`rc=0`**, and a **5.5 MB** screenshot |
>
> ⚠ **The two clues at the bottom of the section remain true** (*«More than 1 GPU vendor detected»*, the
> fenced-off Radeon): ⛔ **they are warnings, not the cause** — the same line comes out even now, with the
> browser working.
>
> ⭐ **And what remains right**: *«the defect is there, the diagnosis is not»*, written here at the bottom on 24
> Aug. ⇒ **It was the exact sentence**, and it is the one that should have been followed instead of closing with a ✅.

### ~~20.1-ter~~ *(the original text, kept)* ✅ Firefox is broken — **and it is not ours**

`[M]` Firefox `140.14.0esr`: alive (80 threads, 126 MB), **zero frames after 90 s**, never attached
to the Wayland socket. It fails identically from `systemd-run --user`, with explicit `--profile`, with
`MOZ_CRASHREPORTER_DISABLE`, `MOZ_DISABLE_GPU_PROCESS`, `LIBGL_ALWAYS_SOFTWARE`,
`MOZ_ENABLE_WAYLAND=0`, sandboxes off.

⭐⭐ **The check that closes the question**: `firefox --headless --screenshot` as **`nicfio`** —
no REMOTIX session, no Wayland, no monitor — **hangs the same way** and is killed at
60 s with an empty profile. ⇒ **Firefox is broken on this machine for everyone, inside and outside REMOTIX.**
It is not a defect of the product, and §14.7/§16.5 must be read this way.

⚠ Two clues for whoever picks it up again: `[GFX1-]: More than 1 GPU vendor detected via PCI, cannot deduce
vendor` (Intel `0x8086/0x4680` + AMD `0x1002/0x73bf`), and `/dev/dri/renderD129` belongs to the group
`remotix-nogpu` — the AMD card is fenced off **on purpose** (§4.6-ter).
⭐ And the `[M]` of 23 Aug (*«the profile is never created in `~/.mozilla/firefox/`»*) looked at
**the wrong place**: Debian `firefox-esr` uses `~/.mozilla/firefox-esr/`. ⚠ That one stays
empty too — the defect is there, the diagnosis is not.

### 20.1-quater ⭐ The tool that was missing — `banchi/09-b82-mostra.sh`

It launches a command inside a user's session with `systemd-run --user` (that is in `app.slice`,
where it would end up when chosen from the menu), then **counts the frames before and after and gives the verdict on that
number** — ⛔ never on *«the process is alive»*. Four guards: a single compositor · a single monitor and
ours · the environment **read** from `systemctl --user show-environment` instead of invented · and
⭐⭐ **G4: is someone watching?** — zero `rete-quic` beats ⇒ **no verdict**.

⭐ **G4 was born from a red on right code**, and it is the guard that would have avoided the three blocked
tests of this morning. Tested in the three directions: `mpv` 240 against 0 (green) · `gnome-terminal` 40
against 1 (green) · `firefox` 0 against 1 (red) · without a client, **it refuses to judge**.

⛔ **And there was nothing to cure in `src/`**: the child prepares the session well — one compositor, one
monitor, scale 1.0, complete environment. The cure was **in the way of judging**.

## 20.2 ⛔⛔⛔ AUDIO — the premise was false, and underneath there was worse

### 20.2-bis ⛔ «36 % of audio does not reach the wire» was a property **of the bench**

`[M]` The 7920 log, **four attaches out of four** of the user's real session:
`negoziato … audio.codec=opus` → `canale audio ACCESO — codec 1 (Opus)`.

⇒ ⛔ **The user was never on PCM.** `[R]` PCM is imposed by **the benches**: `09-b68:191`,
`09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294` all pass `--audio-codec pcm`.
⇒ **§17.2-quater and §18.5 must be read this way**: the 36 % refused and the 2 463 kbit/s are properties of
a **bench configuration**, not of the product in use.

### 20.2-ter ⭐⭐⭐ AND WHAT WAS UNDERNEATH: **589 kbit/s are spent to carry 1.2 kbit/s of silence**

`[M]` What gets refused, on the **real** session: `datagram di 16 byte` = 1 (prefix) + 12
(§6.3) + **3 of payload**. Reproduced on the bench: `codec 1 (Opus), 3 byte di carico`, 1 248 out of 1 248, and
`suono.c` says **`PICCO 0 su 32767`**. ⇒ **Digital silence is being refused.**

`[M]` With a still desktop, Opus: **48.0 datagrams per second out of 48.4 packets** — the wire is *all*
audio — and every packet is **full**, 1 441 bytes out of 1 452, because of the `PADDING`.

**The cure** (`src/audio.c`, ⛔ born **off**, I6): a block in which **all** samples are
exactly zero **does not become a datagram**. ⭐ The reason why it is legitimate: §6.3 puts the `istante`
in every block and the receiver puts it back in its absolute place ⇒ **a block not sent is a hole, and a
hole is silence** — which is exactly what that block contained. ⛔ No threshold: **only digital
zero**, the only case in which «sent» and «not sent» sound identical.

| still desktop, Opus | on the wire | packets/s | datagrams/s | bytes/packet | payload |
|---|---|---|---|---|---|
| **off** | 557.6 kbit/s | 48.4 | 48.0 | 1 441 | 1.18 kbit/s |
| ⭐ **on** | **5.5 kbit/s** | 0.5 | 0.0 | — | 0.00 |

⇒ ⭐⭐ **102.1 times**, and 1 248 blocks silenced out of 1 248. **Today a still session spends 589 kbit/s
to carry 1.2 kbit/s of silence: 99.8 % is padding.**

**The check that protects the user** (440 Hz tone in the sink, judge of `07-b42`): coverage
**1.0000 → 0.9996**, tone purity **1.000 → 1.000**, blocks silenced **1 out of 5 001** — and that one
precedes the first samples. ⚠ Declared price: the client's `mancati` go from 0 to 2 (a wanted hole
leaves the same jump of `istante` as a lost one).

⚠ ~~The switch today is **a build-time one** (`-DAUDIO_SILENZIO_PREDEFINITO=1`) … ⏳ the command
line is **described and not written**.~~
> ✅ **WRITTEN, on 24 Aug 2026** *(realigned to the code on the 28th)*. The `-D` **was removed**, and
> the only road is **`--niente-audio-silenzio`** on the server's command line, which `figlio.c`
> copies at the end of the child's `argv` as it already does with `--parlantina`. ⛔ And it holds for **two
> processes**: the real encoder sits in the child, but the `--audio-prova` tone opens an `audio_cod`
> in the server — if only one were switched on, the two benches would measure two different products.
> ⚠ The reason why there are not two of them: *«two roads for the same cure are two numbers that
> diverge»* (`src/audio.h`).

### 20.2-quater ⛔ TWO DEFECTS FOUND ALONG THE WAY, and neither was looked for

1. ⛔⭐ **`WT_DGRAM_RIMANDI_MAX` does not measure what its comment declares.** `[R]`
   `w->dgram_rimandi` is a field of `struct wt`, that is **of the connection**: it rises at every refused
   pass and goes back to zero only on a success. The comment beside it says *«how many passes in a row
   **the block at the head** has been postponed»* — ⛔ but the head has meanwhile been replaced
   dozens of times. ⇒ **It does not measure the age of the block: it measures how long the connection has not sent
   anything.** `[M]` And that is why the first refusal happened **with the window open**
   (`cwnd_left = 7 424`, and the line itself says *«it is NOT congestion»*).
   ⭐ And the refusals are **in bursts, not scattered**: outside the burst 0.004 %, **inside 100 %** — 100
   refusals every 2.00 s = every block produced, for twenty seconds. Not scattered clicks: **twenty seconds
   of nothing**.
2. ⛔ **«Audio must not be starved by video» IS NOT WRITTEN ANYWHERE.** `[R]` Searched
   in `SPECIFICHE.md` (§10 and the invariants), `RCP.md` §6.3, `DECISIONI.md`, `CODER.md`: **nothing**.
   The only place where the question is decided is the code — `wt_scrivi():7286`, *«DATAGRAMS BEFORE
   STREAMS»*. ⇒ ⚠ **A decision taken in the code and never put on record**, and it is precisely
   the kind of thing this phase exists to discover.
   `[M]` And today **audio** wins: with a still desktop the wire is all its own; on the real session with the
   desktop moving it takes **25-33 %** of the packets.

### 20.2-quinquies ⛔ AND A PREDICTION OF THE AGENT THAT DID NOT HOLD — written as it is

`casa-cattiva`, scene with the tone, same `netem`, cure off:

| codec | on the wire | sent | refused | ‰ | **coverage** |
|---|---|---|---|---|---|
| PCM | 1 024.5 kbit/s | 3 135 | **1 880** | **375‰** | 0.6088 |
| Opus | 366.3 kbit/s | 1 127 | **126** | **101‰** | **0.8803** |

⭐ Coverage rises **0.61 → 0.88** (+27 points of audio that really arrives). ⛔ But the predicate
asked for *«Opus below 20‰»* and gave **red**: Opus divides the refusal by 3.7, **it does not remove it**.
⇒ **The codec is the cure of the cost, not of the refusal.** The border was left where it was and the red
written in the bench, instead of retuning the threshold after seeing the number.

### 20.2-sexies ⏳ The half cure described and not written — the `PADDING`

`dgram_scrivi_uno()`, lines **1613** and **1647**: `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING` must be
**conditioned** on there really being a batch to compose (more than one datagram in the queue, or video bytes
to slip in). With **one** datagram only and the video queue empty the GSO batch is one packet
and the padding **buys nothing** — it costs 1 425 bytes out of 1 441. ⛔ **It is not removed, it is
conditioned**: the box at `:1581` explains why it is there (a short first packet makes the
GSO batch collapse).

## 20.3 ⭐⭐⭐ THE AUDIO-VIDEO MISALIGNMENT — the number holds, **the reading does not**, and it can be heard

`banchi/09-b85-*` · binary `64258ca4…`. ⛔ **And the yardstick was certified before measuring
anything**, in three steps, none skipped.

**(a) on the file**, 7 known offsets injected with `-itsoffset`: found again **−700.0 · −300.0 · −100.0 ·
−0.0 · +100.0 · +300.0 · +700.0**. **(b) resampled at 40/s**, 4 phases: bias **−2.3 ms**, amplitude
**4.0 ms**. **(c) ⭐⭐ through the real product**, the same film with the audio shifted by known ±300 ms,
played in the session and captured from the wire:

| set | found (n=23) | error |
|---|---|---|
| **+300** | **+288.5** | −11.5 |
| **0** | **−12.6** | −12.6 |
| **−300** | **−310.8** | −10.8 |

⇒ **slope 0.9988, constant −11.6 ms.** The yardstick finds again what one knows one has put in, with the right
sign, over the whole chain.

### 20.3-bis ⭐⭐ THE PRODUCT IS CLEAN — **no +331, no +690, in any case**

`[M]` 24 Aug (sign: **positive = the sound comes out AFTER the image**, the convention of
`pagina.html` · `avvia_audio()`):

| case | fps | video Mbit/s | **offset at the source** | **offset on the network** | network p90 |
|---|---|---|---|---|---|
| still | 40.1 | 0.30 | **−12.6** (n=23) | −5.8 | −3.9 |
| under load | 35.1 | **106.5** | **−7.8** (n=22) | −14.7 | −16.6 |
| loss 1 % | 36.5 | 0.30 | **−12.7** (n=22) | −6.1 | −9.8 |
| loss 5 % | 16.2 | 0.60 | **−17.2** (n=10) | −19.1 | **−94.9** |

⇒ **All four within ±6 ms of the certified constant.** The product stamps the two streams with the
same clock and stamps them well: **the offset is not born before the browser.**

⭐ **And the hypothesis «it gets worse with loss» is refuted on the median**, confirmed only on the tail: at
5 % the video p90 latency goes to **118.5 ms** against 23.6 for audio (streams retransmit,
datagrams do not) ⇒ **−94.9 ms**, that is **audio running ahead**, not audio lagging behind.
⚠ And half of the clapperboards disappear: **11 flashes out of 20 clicks**.

### 20.3-ter ⭐⭐⭐ THE +331 IS NOT AN ARTEFACT: **it is the audio cushion, and it is written in the product**

`[R]` `src/pagina.html` · `AUDIO_CUSCINO_MS()` `AUDIO_CUSCINO_MS = 250` · `:5564` `AUDIO_CUSCINO_MAX_MS = 600` ·
`:5761` `aoff = (perf − ist/1000) + CUSCINO + u`.

> ⇒ `AV ≈ cuscino + latenza d'uscita − ritardo di pittura`

At rest 250 → **~331**; under load the queue exceeds 600 and `a.base` **re-anchors** (`:6152`) →
**~690**. ⭐ **The two numbers of §16.4 are the two notches of the cushion**, not two measurements of a defect.

⛔⛔ **And §16.4 reads the sign backwards.** It writes *«sound precedes the image»*; the product
says *«positive = the sound comes out AFTER»*. ⇒ **Audio is LATE, not early** — and the two things
have **very different** perceptual thresholds.

⚠ **And `AV` cannot see the half measured here**: it cancels the server's `istante` from both
terms. ⇒ A product with a green `AV` can be desynchronized, and vice versa. The two measurements **do not
overlap**, and together they say that the offset lives **entirely inside the page** — which is the place where
it costs least to cure it.

### 20.3-quater ⛔ IT CAN BE HEARD — and the source is cited

**Rec. ITU-R BT.1359-1** (*Relative timing of sound and vision for broadcasting*, 1998), clause g)
and Note 1: *«detectability thresholds are about +45 ms to −125 ms and acceptability thresholds are
about +90 ms to −185 ms on the average, a positive value indicates that sound is advanced with
respect to vision»*.

⚠ **The ITU sign is the opposite of ours**: for them positive = sound **early**. Our
+331 (audio **late**) is ITU **−331 ms**.

| | ITU threshold (audio late) | §16.4 at rest (−331) | §16.4 under load (−690) |
|---|---|---|---|
| **it is noticed** | −125 ms | ⛔ **2.6× beyond** | ⛔ **5.5× beyond** |
| **it is acceptable** | −185 ms | ⛔ **1.8× beyond** | ⛔ **3.7× beyond** |

⇒ ⛔⛔ **If the +331 is what the user receives, it is noticed and it is not acceptable.** ⚠ That the user
did not judge it on the grain **does not say it does not bite**: it says that that scene did not allow
judging it — and it is the **second** of the two readings kept open in §16.4, not the first.

⏳ **What remains**: the `AV` half has not been remeasured (it wants the browser, and on that machine
Firefox does not start — §20.1-ter). Everything that sits **before** the browser is clean; the direct
confirmation of the 331 waits for that instrument.

> ### ⭐⭐⭐ AND THE JUDGEMENT HAS ARRIVED — **25 Aug 2026, phase 10**
>
> ⛔ *The reason why this `[?]` had stayed open was false*: Firefox **was not broken**, it was
> `~/.cache -> /tmp` (§20.1-ter, **refuted**). ⇒ With that removed, the browser starts, and the test could
> be done.
>
> ⭐ **And the user judged it on the hardest scene there is** — a **4K** video inside the
> remote desktop, with his tablet's bandwidth throttled to **10 Mbit/s**, that is **below the declared
> floor**:
>
> > *«Il video mostra degli artefatti, ma è normale: siamo sotto le specifiche. Però **audio e video
> > fluidi e in sync**.»*
>
> ⇒ ⭐ **The `AV` half of the sync has its judgement.** ⚠ **Not a number**: a judgement — the
> `[M]` of the **331 ms** and the Opus term remain `[?]`, and for those the instrument is still needed.
> ⭐ But the question that counted — *«to the ear and to the eye, do they go together?»* — has an answer, and it
> is **yes**, taken where the yardstick is the user (**I8**).
>
> `[M]` And beside the judgement there are the numbers of the same scene, read from the log without touching it:
> **37.4 fps**, **3.20 Mbit/s**, ⭐ **empty queue** — bandwidth **halved without losing a
> frame**. ⇒ `fasi/10-multi-tenant-e-il-budget.md` §10. ⚠ And the round is in **PCM**: the Opus term is not inside it
(in the repo there is no Opus decoder, `07-b42-giudice.py` · `main()`).

⭐ **The clip is there, and it is what the user needs to give his judgement**:
`/media/REMOTIX/tmp/09nr10/film/09-b85-claquette-calma-p000.mp4` (70 s, **34 claps**), with the twins
`-p300`/`-m300` at known offset, and `-dura-` for the case under load. Server **7973 is on**.

---

# §21 · ⭐⭐⭐ THE CLOSING — *24 Aug 2026*: the cures are switched on, and the word «bistable» falls

## 21.1 ⭐⭐ THE USER'S JUDGEMENT ON SYNC — **blind, and the yardstick was his ear**

⛔ **The test of §16.4 had failed because of a design error of mine**: I had asked for a judgement on
sync while watching **pure grain**, that is the image with the fewest possible holds. ⇒ Redone with the
clapperboard of §20.3 — a board that slaps, **34 times in 70 s** — and ⭐ **blind, with three
twins**, without telling the user which was which.

| order | what was **in the file** | his judgement |
|---|---|---|
| 1st | audio **321 ms early** | *«perfetto»* |
| 2nd | **aligned** (21 ms) | *«perfetto»* · *«il bip è in sincrono con il flash»* |
| 3rd | audio **279 ms late** | ⭐ *«il flash è in anticipo rispetto al bip»* |

⭐⭐ **He recognized the real delay, with the right direction, without knowing it.** ⇒ His ear is
**calibrated** on this scale, and his judgements count — which is precisely what §16.4 lacked.

⛔ **And the verdict is that the defect does not arrive.** The **aligned** clip reached him **in
sync**. If the product really added the **+331 ms** of §16.4, that clip would have
sounded to him **like the third** — recognizable, because he has just shown he recognizes 279 ms.
⇒ **The delay that reaches the ear is below the threshold he can recognize**, that is **< ~280 ms**,
and probably much less.

⚠ **What this does NOT say**, and it must be written: between the 1st and the 2nd he saw no difference, and they are
**321 ms** apart. ⇒ On the **early** side his resolution is coarser than 300 ms. But the
cushion pushes towards the **late** side, and it is there that he discriminates. ⚠ And the round is in PCM: the Opus
term is not inside it.

⇒ ⭐ **§20.3-quater must be read with this beside it**: the count with the ITU threshold says *«it would be heard»*
**if** the 331 ms arrived. `[M]` The ear says that **they do not arrive**. The two things do not
contradict each other: §20.3 measures the cushion **inside the page**, and the video's painting latency
compensates for it to a large extent — the part that **neither of yesterday's two measurements could see on its own**.

⛔ **And a correction of mine, taken and withdrawn in three minutes**: after the first two *«perfetto»* I had
concluded that `mpv` put the streams back in sync and that the test was **void**. ⚠ It was a
hasty conclusion on two data points: **the third judgement refuted it**. I write it because the haste to
declare an instrument void is the same defect as the haste to declare it good.

## 21.2 ⭐⭐⭐ «BISTABLE» WAS THE WRONG WORD — it is **a trigger at constant risk**

`banchi/09-b83-biforcazione.py` · `[M]` 24 Aug · cell `perdita-0,20` · **40 rounds** at two durations
· binary `56c62bb0…` · cures off.

**First campaign** (20 rounds of 25 s): spiral **13 times out of 20**. Keyframes **0** in 7 rounds, **≥ 5** in
13, ⛔ **no round between 1 and 4**: two branches, not a wide distribution.

⛔ **And the fact that distinguishes them in the first ten seconds IS NOT THERE: 43 tests out of 43 negative**
(Bonferroni threshold 0.05/43, exact permutation on the rank sum). ⭐ **And it became clear why** —
the ignition instants (first abandon §5.1 at regime):

> **3.1 · 3.2 · 4.3 · 4.5 · 5.3 · 8.0 · 8.8 · 9.5 · 10.5 · 11.4 · 18.4 · 18.6 · 24.9 s**

⇒ **5 ignitions out of 13 fall AFTER the ten seconds.** In that window there was nothing to find
because in those rounds the spiral **had not started yet**. ⚠ The short window was a limit of the
**design**, declared as such and not attributed to the product.

### 21.2-bis ⭐⭐ THE TEST AT TWO DURATIONS — the prediction holds

| round duration | spiral **observed** | **expected** from the constant risk |
|---|---|---|
| **10 s** | **35 %** (7 out of 20) | 31 % |
| **50 s** | **90 %** (18 out of 20) | 92 % |

`[M]` λ = **0.0529 per second**. The pre-registered tests: **T3** — does a single λ explain all three
durations? **p = 0.53**, not rejected. **T4** — is there a shape in time? **p = 0.055**, above the
threshold of 0.0125: no shape.

> ⇒ ⭐⭐⭐ **They are not two behaviours between which the product chooses. It is a ONE-WAY trigger: every
> second has the same probability (~5 %) of igniting, and once ignited it never goes out.**

⛔⛔ **And the consequence is the thing that counts**, because it touches every number of §17:

- **median** time for it to ignite: **13 seconds**;
- in **one minute** of work on that line it is almost certain;
- in **one hour** — which is the real duration of a session — it is **certain**.

⇒ ⚠ **Our benches run for twenty-five seconds; sessions last hours.** Every measurement taken near
the edge of loss **underestimates, and not by a little**: what at the bench appears as *«sometimes
it happens»* on the real desktop is **it always happens, it is just waiting for the moment**.
⭐ And it also rereads the *«è tutto fluido»* of §19.1: those thirty seconds were inside the window in
which, statistically, it has often not yet ignited. ⛔ **It does not refute it** — but it says that **a
long session on that line should be watched before concluding**.

**The hypotheses, one by one** `[M]`: the loss was not the same ⇒ **ruled out** (0.165-0.255 % in
both families) · CUBIC's slow start ⇒ **not verified** (`ssthresh` leaves infinity at
~2 s in both) · the scene ⇒ **ruled out** (first keyframe 58.44-58.88 kB in both) · the three-packet
threshold ⇒ **not verified** · loaded machine ⇒ **ruled out** (CPU 5.1-6.5 % in all 20).
`[R]` The algorithm is **CUBIC** (ngtcp2 1.25, `trasporto.c` · `accetta()` does not touch `cc_algo`) — ⚠ and the test by
contrast **was not done**: it is not exposed by any option.

⚠ **What could not have been seen**, written beforehand: a separation smaller than the
internal dispersion; a rare third mode (36 % probability of not meeting it); and ⛔ **nothing
between one second and the next** — `webtransport.c` · `linea_morta_giudica()` throttles `rete_ciclo()` to one line per second, so
of the slow start one sees the arrival point, **not the run**.

## 21.3 ⭐⭐⭐ THE CURES ARE SWITCHED ON — and on the healthy line **nothing gets worse**

*⇒ `DECISIONI.md` §3.1-septies. «Il prodotto cambia in meglio; questa fase era per rendere più solido
il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli.»*

**The contract — and for each one a single road:**

| cure | default | **only** road to switch it off |
|---|---|---|
| video queue threshold | **100 ms** | `--sgombra-soglia-ms 0` |
| rate regulator | **on** | `--niente-ritmo-adattivo` |
| dead line | **on** (stall 5 000 ms · silence 10 s) | `--niente-linea-morta` |
| eviction of the ghost | **15 000 ms** | `--sfratto-ms 0` |
| audio silence | **on** | `--niente-audio-silenzio` |

⛔ `--ritmo-adattivo` and `--linea-morta` **no longer exist**: whoever types them receives a message that
explains the change and **exit 2**, not a generic help. ⛔ And the `-D AUDIO_SILENZIO_PREDEFINITO` is
**removed**: two roads to switch on the same cure are two numbers that diverge.
⭐ The audio option travels **negated** at the end of the child's `argv` — the road of `--parlantina`
— because the child is an `execve` with the environment composed **from zero**.

⛔⛔ **The startup lines are the record, and none says «SPENTO (I6)» any more.** Each one declares **state ·
number in force · that it is the default since 24 Aug by the user's decision · how to switch it off**, and
`[M]` **the price beside it**. When off they say *«switched OFF by hand … and it is NOT the default»*.

### 21.3-bis ⭐⭐ THE TEST THAT COUNTS — the wound of v1, looked for on purpose

`banchi/09-b86-predefiniti.py` · port 7980 · binary `14561dce…` · **29 cases of `--certifica`**.

- **(a) on by itself** ✅ — server launched **without any option**, and the five cures turn out
  active ⛔ **read from the product's startup lines**, not from the command line;
- **(b) each one can still be switched off** ✅ — five restarts, one at a time; and the two old names **refused**;
- **(c) ⭐ the product works with them on**, paired round of 25 s at 1920×1080:

| arm | frames/s | keyframes | delta share | final drift |
|---|---|---|---|---|
| all **off** | 39.60 | **0** | 1.0000 | 0.0 ms |
| ⭐ **defaults** | **39.69** | **0** | 1.0000 | 0.4 ms |
| `[M]` the anchor of §17.6 | 39.85 | 0 | — | 0.1 ms |

⇒ **No worsening**: −0.2 % against the cures off, −0.4 % against the anchor, **within the declared
noise of 5 %**. Zero keyframes, zero holes, **zero dead-line firings, zero evictions**.
⭐⭐ **It was the test that could have made us withdraw everything** — the wound of v1 is exactly «the numbers
improve and the experience gets worse» — and it is green.

⚠ **And two benches break by construction**, which is intended and must be said: `09-b79-cure.py` typed
`--ritmo-adattivo`, `09-b84-audio-silenzio.py` paired **two binaries** compiled differently. ⭐ Now
the off arm is done **from the command line on the very same binary**: one defendant fewer.
⏳ Being cured.

## 21.4 ⭐⭐ THE TAILS — and two of the three close with a **no**

### 21.4-bis The two benches broken by the change, and a defect found while putting them right

`09-b79-cure.py`: arms **reversed** — **A** = cures off **by hand**, **C** = *no option*.
⭐ The gain is written in the comment: **the arm that represents the product is now the one that is
asked nothing**, and therefore it cannot promise anything. `[M]` `--certifica` 21/21; real round on
`ritardo-30`: fps **38.15 / 39.61 / 39.78**, keyframes 0.2 / 0.0 / 0.0 %, **S′ green**.

`09-b84-audio-silenzio.py`: from **two binaries** to **one**. ⭐ Two binaries were **two defendants** — if the
arms gave equal numbers the explanations were two (*«the cure is not needed»* or *«the binaries were not
the ones I believed»*); a single one leaves one.
⛔⭐ **And while simplifying it a real defect popped out**: the line of the **off** arm now
contains *«since 24 Aug it is born ON»*, and the bench looked for `"ACCESA" in dett` ⇒ **it would have read
«on» on an off arm**, giving green to two wrong arms **precisely now that that predicate
is the only belt**. Cured by anchoring it to the two state sentences.
`[M]` `--certifica` 31/31; `muto` round (Opus, still): **557.5 → 5.7 kbit/s = 97.3×**, 1 248 blocks
silenced; `tono` round (PCM): coverage **1.0000 → 1.0000**, purity **1.000 → 1.000**, silenced **1 out of
5 002**.

### 21.4-ter ⛔⭐ `WT_DGRAM_RIMANDI_MAX` — **the quantity is kept, the unit is changed**

`[M]` The number that explains everything: `casa-cattiva`, 25 s ⇒ **2.2 million postponements**, that is **~85 000
write passes per second** under load against **~200** at rest. ⇒ The `4096` cap was worth
**~48 ms** in one case and **tens of seconds** in the other. ⛔ And it was not a fuse, **it was the
policy**: 2 258 blocks thrown away by that cap against **9** by the full queue — **99.6 %**.

⭐⭐ **The obvious road was tried and the measurement refused it.** Timestamping every block and throwing it away
on its **real age**: `[M]` at 50 ms it does not fire more than it fires at 250, because the queue holds 8
blocks = 40 ms of PCM and **the head is almost never older than 40 ms**. Price of that «touches
nothing»: **+30 % of bytes on the wire** (1 415 → 1 840 kbit/s, **stolen from the video's window**) for
**+11 % of useful blocks** — the rest arrives already old and **the client throws it away**.

⇒ The field becomes **`dgram_zitto_da`** («how long the connection has not put a datagram into a
packet») and the cap **`WT_DGRAM_ZITTO_MAX_MS`**, in milliseconds. ⛔ And `4096` **is not converted with
a division**: it is self-referential — how many passes are made depends on how much is thrown away. `[M]` With the
product 2.1 M postponements, with the cap at 50 ms **20 M**. ⇒ The value was **tuned on the measurement**, and the
green is *«indistinguishable from the product»*:

| cap | sent | thrown (queue) | refused | kbit/s | useful | useful/wire |
|---|---|---|---|---|---|---|
| **the product** (5 rounds) | 2 912-3 242 | 14-16 | 1 753-2 084 | 1 312-1 447 | 1 223-1 315 | 0.40-0.44 |
| ⭐ **10 ms** | 2 947 | 16 | 2 039 | 1 286 | 1 246 | 0.435 |
| 5 ms | 2 999 | 15 | 1 995 | 1 327 | 1 246 | 0.424 |
| 50 ms | 3 955 | **797** | 263 | 1 743 | 1 390 | 0.360 |

**10 ms** (= two PCM blocks) lies **inside the product's dispersion on every column**.
⇒ ⭐ **The cure changes what the number means, not what the product does.** The real age of the
block stays recorded (`dgram[].nato`) but ⛔ **does not decide**: it ends up in the log line beside
the silence, **on purpose to be refuted**.
⏳ To be carried over into `rcp.c`: the «final count» still says *«refused by ngtcp2»*, and now they are
*«thrown away because the wire had been mute for N ms»*.

### 21.4-quater ⛔ THE `PADDING` — **NOT done, and the diagnosis was wrong**

Written, built and measured paired (still desktop with the tone, smooth `lo`, same binary except for
that line):

| codec | padding | kbit/s | bytes per packet |
|---|---|---|---|
| Opus | always | 557.7 / 556.5 | 1 441 |
| Opus | conditioned | 556.9 / 555.8 | 1 441 |
| Opus | ⛔ **never** | 556.4 | ⛔ **1 441** |
| PCM | always | 2 221.7 | 1 443 |
| PCM | conditioned | 1 988.0 | 1 292 |

⛔⛔ **On Opus the gain is ZERO, not «small»**: with padding **never requested** the packet stays
at **1 441 bytes**. `[R]` **What fills it is `wt_scrivi()`**, which asks for padding at *every* stream
write and closes the packet the datagram had left open with `WRITE_MORE`. ⇒ **The
padding of a still session belongs to the STREAM, not to the datagram**, and whoever wanted to remove it must
go there.

⚠ On PCM the condition bites (**−10.5 %**) only because at 200 blocks/s the datagram closes the packet
by itself — but PCM **is not what the product negotiates**, and with silence on and a still desktop the
datagrams are **0.0/s**. ⇒ **Code reverted**, and the record with the numbers stays in the
`MORE`/`PADDING` box of `webtransport.c`: ⭐ a cure that buys nothing is **more code to
maintain**, and it must be refused with the numbers beside it instead of forgotten.

### 21.4-quinquies ✅ And the decision never put on record is now in `SPECIFICHE.md` §10.1

⛔ *«When the window narrows, audio goes ahead of video»* was a product policy
taken **in the code** (`wt_scrivi()`) and **written in no document**. ⇒ Now it is `SPECIFICHE.md`
**§10.1**, with the reason (the two loads do not degrade in the same way), the price (bandwidth taken
from video precisely when there is little of it) and the limit **by construction** (the datagram queue is
eight long ⇒ at most eight packets go ahead).
