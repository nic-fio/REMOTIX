#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b79-fixes — THE TWO CURES OF THE SPIRAL, PAIRED ON A NETWORK THAT LOSES.

    port 7940 · probes 7949..7945 · user `provanr4` (uid 1040)
    tree `/media/REMOTIX/src/09nr4-src` · work `/media/REMOTIX/tmp/09nr4`
    unit `remotix-7940` · its own ban-file and socket

═══════════════════════════════════════════════════════════════════════════════
⛔ WHERE IT COMES FROM — and they are numbers, not intentions
═══════════════════════════════════════════════════════════════════════════════

`09-b76-rete-cattiva.py` closed `[M]` on 23 August 2026 the bad-network
grid, with **all cures off** (the defaults, invariant I6), and five
profiles out of eleven are red.  The mechanism, read from the server log:
`abbandonato_in_coda` = `abbandonati` = `chiave_aspetta` at every red profile,
with `delta_non_spedito` at 550-800.  ⇒ The chain is:

    the wire delays → the send queue grows → §5.1 abandons the deltas
    → §5.2 switches on the debt → a keyframe is requested → the keyframe fills the
    window → it starts again.

⭐ It is **the spiral**, and at `loss-3` it makes 87 keyframes out of 87 frames — the same
   face as the defect of 21 August (144/144).

⭐⭐⭐ AND THE CURE FOR THIS SPIRAL IS ALREADY WRITTEN AND TESTED.  Two
      switches, and they have a MANDATORY ORDER (`src/webtransport.c`):

  · the QUEUE THRESHOLD.  `video_clear_out()` without a threshold abandons the deltas **at
    every frame**; with the threshold it abandons them only when the queue is really
    hopeless (`byte × smoothed_rtt / cwnd` above N ms).  ⛔ It is the
    prerequisite of the other.
  · the RATE REGULATOR: instead of abandoning, it slows down capture.
    ⛔ It comes AFTER the threshold, because as long as `video_clear_out()` empties the queue at
    every frame the quantity it hooks onto (`arretrato`) is **zero by
    construction**, and a mute regulator and a healthy line look the same.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ ON 24 AUGUST 2026 THE DIRECTION OF THE SWITCHES WAS REVERSED, AND THIS
      BENCH WAS **BROKEN** — not «to be updated»: broken, that is unable to give
      red
═══════════════════════════════════════════════════════════════════════════════

`DECISIONS.md` §3.1-septies: the user looked at the cures on the real desktop and
decided they are born **ON** in the product.  ⇒ The new contract:

    video queue threshold     ON at 100 ms      turned off with `--clear-threshold-ms 0`
    rate regulator            ON                turned off with `--no-adaptive-rate`

⛔ `--ritmo-adattivo` **no longer exists**: whoever types it gets exit 2 with a
   message explaining the change (`main.c:1211`).  ⇒ Yesterday's arm C —
   the one that typed it — would not have started the server, and a bench that
   does not start does not give red: it gives «ground».  ⚠ It is the worst form of fault of
   a bench, because it looks like a fault of the machine.

⇒ **THE ARMS HAVE BEEN REVERSED**, and the new direction is the one that follows.

⭐⭐⭐ AND THERE IS A GAIN TO CASH IN, which is not cosmetic: **one suspect
     fewer**.  Before, the two arms were the same binary with different options;
     they still are, but the OFF arm — the term of comparison — is
     obtained **from the command line on the very same binary of the product
     that ships**.  ⛔ Before, the «cures on» arm asked for an option
     the normal product never used: if the binary had been the
     wrong one, the option would have been refused and I would have noticed — but if
     it had been the RIGHT one with a different default, I would not.  ⇒ Now the
     arm that represents the product is `""`: no option, no
     promise, just the product.

⇒ The question of this bench: **do those two cures switch off the spiral on a network that
  loses and flutters, and at what price?**

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ PAIRED MEANS **ONE THING ONLY CHANGED**
═══════════════════════════════════════════════════════════════════════════════

Same profile, same duration, same canvas, same scene, **same binary**, and
only the server switches change.  Three arms per profile, and since
24 August 2026 they are **reversed** compared with yesterday:

    A   --clear-threshold-ms 0 --no-adaptive-rate
        ⛔ the TERM OF COMPARISON: the two cures switched off BY HAND.  It is the product
           up to 23 August 2026, byte for byte, obtained from today's binary.
    B   --clear-threshold-ms 100 --no-adaptive-rate
        ⭐ the threshold alone — the middle step, which serves to say WHICH of the two
           cures does the work.
    C   (no option)
        ⭐⭐ THE DEFAULTS, that is the product that ships.

⭐ And the threshold is written out in full in B too, where it would be the default: a
   command line that says what it wants can be reread in a month; one that
   relies on a default is reread wrongly the day the default
   changes — which is precisely what happened today.

⛔⛔ AND ARM **A** IS REMEASURED TODAY, not taken from the table of
    `09-b76`.  Those numbers come from another binary (HEAD, which does not
    even have the two options) and from another hour: using them as arm A would be
    comparing two different things and calling it pairing — and it is exactly the
    most polite way in which a grid lies (`LESSONS.md` §1.26).

⭐ THE ORDER INSIDE THE PROFILE IS A-B-C, one right after the other, not A-A-A then
   B-B-B: so between the three arms of the same profile three minutes go by, not
   twenty, and the machine is the same machine.  ⚠ It costs 21 server restarts;
   twenty seconds each, and it is the price of pairing.

⛔⭐ AND EVERY ARM IS CHECKED FROM THE SERVER LOG, not from what I
    wrote on the command line (`LESSONS.md` E1, «written is not in
    force»).  At startup the product ALWAYS writes — on and off — the two
    lines that say the value in force (`clear_out_declare()`,
    `wt_adaptive_rate()`), and this bench rereads them and stops if they do not
    match.

═══════════════════════════════════════════════════════════════════════════════
⛔ THE SEQUENCE OF AN ARM, and every step has a reason
═══════════════════════════════════════════════════════════════════════════════

 1. **the network is put back smooth**;
 2. **the server is restarted** with the arm's options, and the two startup lines
    are reread;
 3. **a short session is triggered** — the stage and the monitor are born with the first
    client, and the scene would not know where to draw.
    ⛔⭐ And it is triggered **ON A CLEAN NETWORK**, on purpose: `09-b78-opening.py` has
        measured that a **lost** goodbye and a goodbye **never said** are the same
        fact for the server, and the slot stays taken for `SILENZIO` = 30 s
        (`src/rcp.c:263`) — eleven `FAREWELL 0x0F` in a row, `[M]` 23 August.  If
        I triggered under the fault, the next run could find the slot
        taken and I would report as «the cure does not work» a thirty-second
        lock.
 4. **the profile is installed** (`del root` + `add`, never `change`: `[M]` 23 Aug,
    `tc qdisc change` is sticky), the verbs are reread, the two
    `u32` filters of the probe are put back;
 5. **the probe** — 8 000 numbered packets through the same `netem`: was the
    fault put in or not?  ⛔ And it is redone at EVERY arm, not once per
    profile: a number without its verified fault next to it is not a measurement;
 6. **the run**, 25 s, 1920×1080, scene `barra`;
 7. the `qdisc` counters around the run are read, and the `quic-net` lines
    of the log (`cwnd`, `srtt_us`, `pto_us`, `dgram_lost`, `dgram_spurious`,
    `judgement=`), which are there in the working tree and not in HEAD.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE REVIEW OF THE EVENING OF 23 AUGUST — «which numbers were dirtied», CHECKED
═══════════════════════════════════════════════════════════════════════════════

Tonight's three-arm grid ran while `_transcribing_root`
wrapped `NETWORK.root` instead of b70's cured `root` (⇒ the box above
that function).  ⇒ It must be said which numbers that line dirtied, and the answer
is READ, not assumed.  There are three checks, and none is a line of reasoning:

 1. ⭐ **THE LINE DIRTIED NOTHING ON THIS GRID — it was a defect still
    to be collected.**  `[R]` at 19:00 on 23 August `09-b70-ritmo.py` at HEAD
    still had `def root(comando, cap=300): return NETWORK.root(comando, cap)`
    (line 1236): b70's cure is from 19:41, **after**.  ⇒ Wrapping `NETWORK.root`
    was then identical to wrapping `B70.root`, and the defect is PROSPECTIVE —
    it would have bitten the next run, the one with b70 cured.  ⚠ It is exactly the
    reason it must be cured all the same: its face does not change when it starts
    lying.
 2. ⭐ **THE `riga0` WAS THERE, and the server counts are FROM THIS RUN.**  `[R]`
    `09-b76-rete-cattiva.py` at HEAD (line 297) already replaces
    `B70.log_line_list` with its own, which puts the redirect inside a `bash -c`.
    ⇒ b70's defect 2 (the `< file` that steals stdin from `sudo -S`) **did not
    fire**: b79 did not even go through the broken function.
    `[M]` the counter-proof in the numbers, and it is the opposite signature to the cumulative one:
    on all 36 cells `righe_ciclo` sits between **25 and 27** (one 25 s run) and
    `attese_a_vuoto` between **1 973 and 2 156** — constant, not rising.  On
    `delay-30` A-B-C gives 2 015 / 2 006 / 2 016.  The cumulative one is visible at a glance
    (`[M]` b70: 4 041 against 1 604, 2.5 times, and rising): here it is not there.
 3. ⭐ **THE COUNT OF ANOTHER RUN IS STRUCTURALLY IMPOSSIBLE HERE**, and not
    by luck: `[R]` `07-b64-terreno.sh:106` does `: > "$WORKDIR/registro.log"` at every
    `accendi`, and this bench restarts the server at **every arm**.
    `[M]` the counter-proof: no pair of cells carries identical numbers from the
    log, and three cells (`loss-3` A, `burst-heavy` A and B) said
    **«NOTHING TO READ»** instead of reporting the neighbour's number — which is the
    proof that in the window there was no one else's count to steal.

⭐⭐ AND THE THING THAT COUNTS MOST, and it is a division, not an acquittal:
   **the verdict does not go through the log.**  `[R]` `p_spiral_off` (K′),
   `p_rate_restored` (F′) and `p_healthy_line` (S′) read only `n["chiavi"]`,
   `n["frames"]`, `n["quota_delta"]`, `n["fps"]`, `n["fps_finestra_min"]` and
   `n["deriva_*"]` — all from `misura(giornale, …)`, that is from the client's **§11.1
   trace**.  From the server log come the four numbers that
   CORROBORATE (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`,
   `abbandonati`) and nothing else.
   ⇒ «the spiral switches off, but only with arm C: keyframes from 51.7-88.1 % to
     0.0-5.6 %» and «the healthy line pays nothing» are not log numbers, and
     had nothing to be dirtied by.  ⚠ Redoing the five red profiles
     costs an hour and adds nothing (`LESSONS.md`, proportionate process).

⭐⭐ AND ONE CELL ONLY WAS REDONE ANYWAY — `delay-30` with three arms, which
   is the predicate worth most of all («the healthy line pays nothing») and
   costs eight minutes, not an hour.  It is not a doubt about the numbers: it is the only proof
   that the CURED chain really runs all the way, and that the two new guards
   fire.  `[M]` 23 August 2026 evening, same binary (md5 `eee17f40…`):

     arm        fps    worst s     keyfr.   drift end     drift max
        A     39.94/s     37.0      0.0 %      0.0 ms      10.1 ms
        B     39.94/s     36.0      0.0 %      0.2 ms      11.0 ms
        C     39.32/s     34.0      0.0 %     -0.1 ms       6.2 ms

   ⇒ **S′ GREEN**: the three arms are indistinguishable (B at 100 %, C at 98 %,
     within the 5 % noise), zero keyframes everywhere, the drift does not move.
     ⭐ And it holds up against the 19:00 run (39.85 / 40.19 / 39.63): the same
       answer eight minutes apart.
   ⭐ The counter-check in the server counts, which is the one that closes the question: the
     spiral lines of arm A come back **identical** to those of 19:00
     (`chiave_aspetta` 1, `delta_non_spedito` 5, `abbandonato_in_coda` 1) and
     `attese_a_vuoto` gives 2 019 / 2 016 / 2 025 against 2 015 / 2 006 / 2 016.  A
     cumulative number does not reproduce; these do.
   ⭐ And the new guards spoke: `riga0` = 205 / 219 / 229, `p_log_read`
     GREEN on all three, `conti_finali` `[2, 4]` in every arm — that is the two
     counts of the trigger session had already settled and the run wrote two OF ITS OWN.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE PREDICATES OF THE PAIR — WRITTEN FIRST, and they return `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

Those of the single run are IMPORTED from `09-b70`/`09-b76` and not rewritten
(`p_nothing_detach`, `p_degrades_over_time`, `p_fault_set`, `p_my_queue`).  The
three that belong to this bench look at the **pair**, which does not exist there:

  **K′ · THE CURE SWITCHES OFF THE SPIRAL.**  The arm's keyframe share goes back
  below 0.10 where arm A had it above.
  ⚠ The threshold is not chosen here: it is the complement of `QUOTA_DELTA = 0.90` of
    `09-b70`, that is §3.3 read backwards.  Two thresholds for the same fact
    are two thresholds that diverge.
  ⛔ And it is SILENT if the spiral was not there in A: putting out a fire that is not there
     is not a merit, and it is a green that would award itself.

  **F′ · THE CURE GIVES BACK RHYTHM.**  The arm's frames/s against those
  of A, with the threshold and the reason written:
  ⚠ `09-b70` estimates at **5 %** the noise between two runs of the same machine.  ⇒
    Below a **10 %** difference — twice the noise — this bench
    **does not judge**: it says «indistinguishable», which is an outcome and not a green.
    Above 10 % upwards it is green; above 10 % downwards it is RED, because a
    cure that takes rhythm away where it meant to give it is the most important discovery that
    could come out of here.

  **S′ · THE CURE DOES NOT COST ON THE HEALTHY LINE.**  ⛔ It is the predicate worth more
  than all the others put together: on `delay-30` — which loses zero, reorders
  zero, and only arrives late — the three arms must be **indistinguishable**.
  The tolerances, each with its why:
    · frames/s within **5 %**, which is the noise `09-b70` measures between
      two runs of the same machine: within that there is nothing to see;
    · keyframe share below **0.10** in all three, as above;
    · final drift that does not grow by more than **the threshold itself** (100 ms).
      ⭐ And this number is not arbitrary: the cure keeps a delta until the
      queue is hopeless for more than N ms, so the delay it can
      add is N by construction.  If it adds more, it is not the
      threshold at work — it is something else, and it must be looked at.

  ⚠⚠ **AND THE PRICE IS MEASURED, NOT ONLY THE GAIN.**  The queue threshold
  **keeps** frames instead of throwing them away ⇒ the **drift** can grow.  ⭐
  The drift is ALWAYS reported next to frames/s: a cure that doubles
  the rhythm and triples the delay **is not obviously an improvement**, and it is
  a choice that belongs to the user, not to this bench.  ⇒ Here there is no
  predicate «B is better than A»: there are the two numbers, side by side.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ `burst-heavy` — «SESSION DETACHED AT 0.3 s OUT OF 25», and the word is wrong
═══════════════════════════════════════════════════════════════════════════════

`09-b76` gives red on `burst-heavy` with the predicate `p_nothing_detach`, which says
*«delivery lasted 0.3 s out of 25 requested: it detached»*.  ⛔ But that
predicate does not look at the connection: it looks at **how long the delivery of
frames lasted**, and the two things are not the same.  ⇒ The `detach` step of this
bench asks **who** detached, and asks four independent witnesses:

  1. **the client**, which says it by itself and in full: `01-b3-client.py:1979`
     prints *«⭐ still attached after N s: nothing dropped»* and returns 0, or
     *«⛔ I did NOT stay attached: …»* and returns 4;
  2. **the server log**: `farewell reason=0x..`, `the client takes its farewell`,
     `slot DENIED`, `BANNED`, and the video «final count»;
  3. **the `quic-net` lines**: `cwnd`, `cwnd_left`, `judgement=` — if the window
     closed and never reopened, the session is alive and **mute**, which
     is a fact different from detaching and needs a different name;
  4. ⚠ **the third possibility to rule out explicitly**: at 13 % clustered loss
     the HANDSHAKE might not complete, and «it never
     opened» and «it detached» look the same.  ⭐ It is told apart by the
     client itself, which prints `SESSION` only when the session is open;
     and `09-b78-opening.py` has already measured `[M]` that up to **25 %**
     independent loss the session opens 10 times out of 10 in ~1.3 s.

⛔ `IDLE_MS` in `src/transport.c` is **30 s**: at 0.3 s it is not that, and indeed the
   `detach` step rereads it from the source instead of trusting this line.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ WHAT THIS BENCH CANNOT SEE
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **THE IMAGE.**  It counts frames, keyframes, bytes and delay.  «It looks
    better with the cure on» is a verdict of the user on the real desktop.
 2. ⛔ **WHICH ARM IS BETTER.**  See the price, above: it is a choice,
    not a measurement.
 3. ⛔ **THE REAL NETWORK.**  `netem` on `lo`: no radio, no router.
 4. ⛔ **THE BROWSER.**  The client is `01-b3-client.py`, which takes the bytes from the
    wire and does not decode: frames/s are a **ceiling**.
 5. ⚠ **ONE RUN PER CELL.**  Twenty-one cells of 25 s are already half an hour
    of lock; a difference below 10 % cannot be told from noise, and
    that is why F′ stays silent there instead of judging.

═══════════════════════════════════════════════════════════════════════════════
⭐⭐⭐ WHAT CAME OUT — `[M]` 23 August 2026, port 7940, Intel UHD 730
═══════════════════════════════════════════════════════════════════════════════

⚠ AND THE LETTERS OF THIS TABLE STILL HOLD, because the reversal of
  24 August changed **how** an arm is obtained, not **what** it is:
  A stays «both cures off», B «the threshold alone», C «both».  ⇒ Whoever
  rereads does not have to turn their head: the command line changes, not the column.

Binary **md5 `eee17f40b0a5ff79fe3b1b3d060a08ed`** (working tree, not HEAD;
`webtransport.c` md5 `0f63542bf2ebf3617afa5b0a5bfe2371`), 25 s per cell,
1920×1080, h264, free bandwidth, scene `barra`, one run per cell.  Every arm
verified from the product's two startup lines; the fault verified by the
probe at every cell; nobody attached to the ports not mine before or after.

⭐⭐ **THE TWO HEADLINE LINES: THE SPIRAL DOES SWITCH OFF, AND IT IS `C` THAT SWITCHES IT OFF, NOT `B`.
    AND IT COSTS FROM ZERO TO A TENTH OF A SECOND OF DELAY ON THE ORDINARY PROFILES, AND
    FOUR AND A HALF SECONDS ON `burst-heavy`.**

| profile | arm | fps | worst s | keyframes % | drift end | drift max | Mbit/s wire |
|---|---|---|---|---|---|---|---|
| `delay-30` ⭐healthy | A | 39.85 | 36 | 0.0 % | 0.1 | 8.9 | 7.55 |
|                     | B | 40.19 | 37 | 0.0 % | 0.2 | 5.8 | 7.60 |
|                     | C | 39.63 | 36 | 0.0 % | 0.9 | 6.1 | 7.53 |
| `loss-1`   | A | 11.96 | 5 | **51.7 %** | −2.4 | 76.5 | 3.43 |
|               | B | 32.13 | 17 | 6.4 % | 23.2 | 107.8 | 4.84 |
|               | C | **32.85** | 21 | **0.0 %** | −1.6 | 99.3 | 5.11 |
| `loss-3`   | A | 7.34 | 5 | **88.1 %** | −40.0 | 53.4 | 2.17 |
|               | B | 20.63 | 11 | ⛔ 23.8 % | 32.9 | 139.3 | 2.90 |
|               | C | 19.63 | 11 | **0.2 %** | −62.2 | 165.7 | 2.79 |
| `jitter-15`   | A | 10.76 | 6 | **59.2 %** | 11.7 | 102.1 | 3.48 |
|               | B | 25.88 | 9 | ⛔ 12.8 % | −65.7 | 64.0 | 8.06 |
|               | C | 21.48 | 15 | **0.0 %** | 53.8 | 168.4 | 6.63 |
| `jitter-30`   | A | 8.56 | 5 | **73.1 %** | 6.7 | 115.6 | 2.55 |
|               | B | 20.25 | 10 | ⛔ 19.9 % | −5.0 | 277.0 | 5.77 |
|               | C | 16.68 | 12 | **0.0 %** | −116.0 | 180.8 | 4.96 |
| `bad-home`| A | 8.28 | 3 | **72.0 %** | −71.5 | 295.3 | 2.21 |
|               | B | 14.37 | 6 | ⛔ 33.6 % | 152.7 | 238.4 | 3.01 |
|               | C | 13.86 | 4 | **5.6 %** | 102.2 | 284.2 | 3.38 |
| ⚠ `burst-heavy` | A | — delivery stops at **4.4 s** out of 25 | | | | | |
|               | B | 4.25 | **0** | 44.6 % | 24.9 | **7 756** | 0.59 |
|               | C | 4.18 | **0** | 4.4 % | 2.1 | **4 521** | 0.78 |

1. ⛔⛔ **S′ · ON THE HEALTHY LINE THE CURES COST NOTHING.**  39.85 / 40.19 /
   39.63 frames/s — one percentage point, within the declared noise of
   5 % — zero keyframes in all three, and the final drift at 0.1 / 0.2 / 0.9 ms.
   ⭐ It is the predicate worth more than all the others, and it is green.

2. ⭐⭐⭐ **THE SPIRAL SWITCHES OFF, BUT ONLY WITH BOTH SWITCHES.**  The
   keyframe share goes from 51.7-88.1 % (arm A) to **0.0-5.6 %** in arm
   C, on all five red profiles.
   ⛔ Arm **B** — the threshold alone — **is not enough**: it leaves 12.8 % keyframes
      at `jitter-15`, 19.9 % at `jitter-30`, 23.8 % at `loss-3` and 33.6 % at
      `bad-home`, that is above the 10 % of §3.3.  ⇒ K′ is RED on B in
      four profiles out of five and green on C in all five.
   ⭐ The why is read in the server counters: in C `chiave_aspetta` and
      `delta_non_spedito` **collapse** (on `burst-heavy`: 988 → 6 deltas not
      sent, 32 → 0 keyframes waited for).  The threshold alone stops throwing away at
      every frame but the §5.2 debt keeps switching on; the regulator
      prevents it, because the frame does not leave at all.

3. ⭐ **THE RHYTHM COMES BACK, BY 1.7 TO 2.8 TIMES**, and on every red profile: F′ is
   green on B and on C everywhere.  The maximum is `loss-3`, 7.34 → 20.63/s
   (+181 %); the minimum `bad-home`, 8.28 → 13.86/s (+67 %).
   ⚠ And B almost always gives **more** frames/s than C (25.88 against 21.48 at
     `jitter-15`; 20.25 against 16.68 at `jitter-30`), because C slows
     capture on purpose: ⇒ the two arms are not «less good and better», they are
     **more frames with more keyframes** against **fewer frames all deltas**.

4. ⚠⚠ **THE PRICE, AND IT MUST BE READ NEXT TO THE GAIN.**  On the five ordinary
   profiles the maximum drift grows by **−38 … +161 ms** (worst: `jitter-30`
   B, from 116 to 277 ms; on `bad-home` and `jitter-15` B **drops**).  On
   `burst-heavy` it explodes: **from no measurement to 4.5-7.8 seconds**.
   ⛔ On that line C is not obviously better than A: it is *an image that
      moves with five seconds of delay* against *a still image*.  This
      bench gives the two numbers and **does not choose**: the choice is the user's.

5. ⭐ And the bytes on the wire **go up** with the cure (3.43 → 5.11 Mbit/s at
   `loss-1`, 3.48 → 8.06 at `jitter-15`): the line was not saturated, it was
   **wasted** — keyframes were being sent instead of deltas.

6. ⭐⭐ **`burst-heavy`: NOBODY DETACHES.**  See the `detach` step further up and
   the § devoted to it: `[M]` the client stays attached for all 25 s
   («⭐ still attached after 25.0 s: nothing dropped»), the audio arrives for
   the whole run (696 datagrams, purity 1.0000), the server sends no
   `FAREWELL`, no `slot DENIED`, no ban, and the session had opened
   normally (`ADMITTED dopo 1837 ms`).  What stops is **only the delivery of
   frames**.  ⇒ The red of `09-b76` is right as a number and **wrong
   as a word**.  ⭐ And the cures change it: delivery, which in A dies after
   4.4 s, in B and C **lasts all 25 s** (4.2/s with empty seconds inside).

═══════════════════════════════════════════════════════════════════════════════
⭐ THE RUN OF 24 AUGUST 2026 — arms reversed, and the predicate worth most
═══════════════════════════════════════════════════════════════════════════════

`[M]` 24 August 2026, port 7981, user `provanr12`, binary md5
`6ec170c03c6e908eb17d3b056b542813`, `delay-30`, 25 s per arm, one run per
cell.  ⛔ It is not a remeasurement of the grid: it is the proof that the REVERSED
bench really runs all the way and that the three arms come into force.

  arm       options                                        fps    keyfr.  drift
  A         --clear-threshold-ms 0 --no-adaptive-rate  38.15   0.2 %   1.7 ms
  B         --clear-threshold-ms 100 --no-adaptive-rate 39.61  0.0 %  −0.7 ms
  C         (no option — the defaults)                     39.78   0.0 %  −0.7 ms

⭐ **S′ GREEN**: the three arms are indistinguishable on the healthy line (B and C at
   104 % of A, within the noise), zero keyframes, the drift does not move.
⛔ And the three startup lines were reread from the log at every arm: A
   declares «0 ms — OFF» and «regulator OFF», C declares «100 ms — ON,
   it is the DEFAULT» and «regulator ON».  ⇒ The arm without options **is**
   the product, verified and not promised.

EXIT CODES
    0   CONFORMING · 1 NOT CONFORMING (there is a red) · 2 usage/ground/network
    3   ⛔ I HAVE NOTHING TO JUDGE — a run or a predicate refused

Usage (from the laptop):
    python3 benches/09-b79-fixes.py --certify     ⭐ without a machine
    python3 benches/09-b79-fixes.py terrain
    python3 benches/09-b79-fixes.py detach          ⛔ the diagnosis of burst-heavy
    python3 benches/09-b79-fixes.py pair [--seconds 25] [--only loss-1]
    python3 benches/09-b79-fixes.py restore
"""
import argparse, importlib.util, json, os, re, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ MY ISOLATION, WRITTEN BEFORE ANY IMPORT THAT READS IT
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76` and `09-b70` bind their constants to the environment **at import**.
#    Importing them without having set mine first would mean writing into the work
#    of another agent and breaking the port of another bench — and the network is
#    the only thing that, when wrong, hurts those who have nothing to do with it.
# ⛔ 7900, 7910, 7920 are already measured terms of comparison and are NOT
#    touched; 7930/7931/7932 belong to three other agents.  Mine is **7940**.
HERE = os.path.dirname(os.path.abspath(__file__))
MY = {
    "PORT": "7940",
    "ACCOUNT": "provanr4",
    "UID_B": "1040",
    "MACHINE": "nicfio@192.168.0.2",
    "SUDO_PASSWORD": "nicfio",
    "ADDR": "192.168.0.2",
    "WORKDIR": "/media/REMOTIX/tmp/09nr4",
    "TREE": "/media/REMOTIX/src/09nr4-src",
    "INSIDE_TREE": "/srv/src/09nr4-src",
    "INSIDE_WORK": "/srv/remotix/tmp/09nr4",
    "UNIT": "remotix-7940",
    "SHM": "/09nr4",
    # ⛔ The probe port cannot be fixed: `09-b76` lost a whole run
    #    because another agent started a server on it WHILE it
    #    was running.  ⇒ five candidates of mine, and the one free now is chosen.
    "PROBE_PORTS": "7949,7948,7947,7946,7945",
    "OUT": os.environ.get(
        "OUT",
        "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
        "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr4"),
}
for _k, _v in MY.items():
    os.environ[_k] = os.environ.get(_k) or _v

PORT = int(os.environ["PORT"])
ACCOUNT = os.environ["ACCOUNT"]
WORKDIR = os.environ["WORKDIR"]
TREE_DIR = os.environ["TREE"]
UNIT = os.environ["UNIT"]
OUT = os.environ["OUT"]
SUDO_PASSWORD = os.environ["SUDO_PASSWORD"]
MACHINE = os.environ["MACHINE"]
VIETATA = "enp7s0"
DEV = "lo"

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (GREEN, GRAY, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (RED, GRAY, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (YELLOW, GRAY, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _mute(p): return (None, p)


def _load(name, fpath):
    spec = importlib.util.spec_from_file_location(name, fpath)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ALL THE MACHINERY IS IMPORTED — not one line of it is rewritten
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76-rete-cattiva.py` carries the profiles, the probe, the reduction of the
#    arrivals, the rereading of the rule, the `qdisc` counters and 31 green
#    `--certify` cases; `09-b70-ritmo.py` carries the reader of the §11.1
#    trace, the reduction to the five numbers and the predicates of the single run.  Two
#    copies of the same reduction in two files are two reductions that diverge
#    (it is the wound of 16 August, `09-b70` line ~430).
B76 = None
B70 = None
NETWORK = None
LUC = None


def do_import(with_network=True):
    global B76, B70, NETWORK, LUC
    B76 = _load("b76rete", os.path.join(HERE, "09-b76-rete-cattiva.py"))
    if not with_network:
        B76.import_fake()
        B70 = B76.B70
        return
    B70 = B76.do_import()          # ⭐ it is the one that hooks up the network and the lock
    NETWORK = B76.NETWORK
    LUC = B76.LUC
    _hook_root()                 # ⛔ see `_transcribing_root`
    # ⛔⛔ AND THEN WE CHECK THAT THEY TOOK MY ENVIRONMENT, not theirs.
    troubles = []
    for name, my, its in (("port", PORT, B76.PORT), ("user", ACCOUNT, B76.ACCOUNT),
                           ("work", WORKDIR, B76.WORKDIR), ("albero", TREE_DIR, B76.TREE_DIR),
                           ("shm", os.environ["SHM"], B76.SHM),
                           ("dev", DEV, B76.DEV), ("vietata", VIETATA, B76.VIETATA)):
        if str(my) != str(its):
            troubles.append("%s: the module has «%s», mine is «%s»" % (name, its, my))
    if NETWORK.PORT != PORT or NETWORK.DEV != DEV or NETWORK.VIETATA != VIETATA:
        troubles.append("the network module has port %d, dev «%s», forbidden «%s»"
                    % (NETWORK.PORT, NETWORK.DEV, NETWORK.VIETATA))
    if troubles:
        raise SystemExit("⛔ I DO NOT MEASURE: the import did not take my environment — "
                         + " · ".join(troubles))


def root(command, cap=300):
    """⛔ This file's `root` too goes through the CURED chain when there is one.

    ⚠ The commands of this file are all already written inside a `bash -c "…"`
      of their own — it is the discipline of `09-b76` — so here not a number changes.
      But the discipline is a convention, and a convention is forgotten by the
      next one who adds a line: `NETWORK.root` alone would give them a plausible
      `0` instead of an error (⇒ the box above `_hook_root`).
    """
    if _ROOT_CURED is not None:
        return _ROOT_CURED(command, cap)
    return NETWORK.root(command, cap)


# ⛔⛔ THE CLIENT MUST BE LISTENED TO IN FULL, and it is not.
#
#    `09-b70.cur_round()` keeps `coda_cliente = text[-400:]`, which is enough for the
#    five numbers and **not** for the question «who detached»: `[M]` 23 August
#    2026, those 400 bytes hold the three final audio lines and do not hold
#    the line that answers — *«⭐ still attached after 25.0 s»*
#    (`01-b3-client.py:1979`).  ⇒ The first `detach` run refused to
#    judge while holding the answer, cut off.
#
# ⇒ Here the WHOLE output of every command that launches the client is recorded,
#   **without touching b70's file** (there are other agents): its `root` is
#   replaced with one that passes the ball and transcribes.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ AND THAT «PASS THE BALL» IS THE MOST DANGEROUS PLACE IN THIS FILE:
#      **TO WHOM** it passes it decides whether the cures of the file below still hold
# ═══════════════════════════════════════════════════════════════════════════
#
# Until 23 August 2026 this function called **`NETWORK.root`**, that is it skipped
# `09-b70-ritmo.py:root()` and went straight to the step below.  ⛔ It is a defect
# that **cannot be seen by reading either of the two files**: here the line is correct (a
# `root` calling a `root`), and there the cure is written and tested — only
# nobody runs it any more.  It is the second one this project pays for in one evening.
#
# ⛔ `NETWORK.root` (`07-b64-rete.py:238`) is a single `sudo` **in front of the bare
#    command**:  `printf password | sudo -S -p '' <command>`.  From there come two
#    defects, and they are those `09-b70` cured on 23 August:
#      1. `sudo` covers **only the first link** of the chain: in `a && b > c` the
#         `b` and the `>` run as the USER, not as root.  `[M]` the reader of the
#         §11.1 trace was not written, and §11.1 stayed without a referee;
#      2. a trailing `< file` **steals stdin from `sudo -S`** (the redirect belongs to the
#         shell and goes to the LAST command of the pipeline, which is `sudo`): the password
#         does not arrive, `sudo` exits 1, and the number comes back **0 in silence**.  `[M]`
#         `log_line_list()` returned 0, `server_counts()` read the log
#         **from server startup** instead of from the run, and `attese_a_vuoto`
#         became cumulative: 4 041 against 1 604 on a still run, 2.5 times.
#
# ⭐ `09-b70.root()` cures both with a single line — `chain_root()`, that is
#    **one** `sudo` and the whole chain inside ITS `bash -c`.  ⇒ Whoever wraps to
#    transcribe must wrap **that one**, or brings the two defects back in
#    by going through a function named like the cured one.
#
# ⛔⛔ AND WRITING `B70.root` IS NOT ENOUGH: when this file arrives, `B70.root` **has
#     already been replaced** by `09-b76-rete-cattiva.py:416`, with a wrapper
#     that in turn calls `NETWORK.root`.  Wrapping `B70.root` then would
#     mean wrapping someone else's defect and calling it a cure.  ⇒ The cured
#     chain is rebuilt **from its pieces** — `B70.chain_root` + `NETWORK.rem` — which
#     are what `09-b70.root()` does, and do not go through any substitute.
#
# ⚠ And it is hooked ONCE ONLY: `pair_up()` does 21 cells in the same process
#   and `do_import()` can be called more than once.  A repeated wrapper
#   does not get the numbers wrong, but it nests 21 calls and the first diagnosis
#   becomes unreadable.
LAST_CLIENT = {"text": ""}
_ROOT_CURED = None


def _hook_root():
    """Installs the transcriber ON TOP OF b70's cured `root` — once only."""
    global _ROOT_CURED
    if _ROOT_CURED is not None:
        return
    if not hasattr(B70, "chain_root"):
        raise SystemExit(
            "⛔ I DO NOT MEASURE: «09-b70-ritmo.py» has no `chain_root()`, that is it is the "
            "version with `sudo -S` in front of the bare command.  On that one a "
            "trailing `< file` steals the password from sudo and the server counts "
            "become cumulative from startup (2.5 times, `[M]` 23 Aug 2026). "
            "Align the tree before measuring.")
    _ROOT_CURED = lambda c, cap=300: NETWORK.rem(B70.chain_root(c), cap)
    B70.root = _transcribing_root


def _transcribing_root(command, cap=300):
    rc, out, err = _ROOT_CURED(command, cap)
    if "01-b3-client.py" in command:
        LAST_CLIENT["text"] = out + err
    return rc, out, err


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE THREE ARMS — and the arm is CHECKED from the log, not from the line
# ═══════════════════════════════════════════════════════════════════════════
#
#   (label, server options, expected threshold in ms, expected regulator)
#
# ⛔⛔⭐ THE DIRECTION IS REVERSED SINCE 24 AUGUST 2026, and the line that counts is the
#      third: **arm C has no options**.  Until 23 August it was the
#      opposite — A was `""` (the defaults, then off) and C typed
#      `--ritmo-adattivo`, an option that today **no longer exists** and makes
#      the server exit with 2.  ⇒ This bench, not reversed, would have measured
#      nothing: it would have said «the server did not start», which looks like a
#      fault of the machine and not like a bench to be updated.
#
# ⭐ And the reversal brings ONE SUSPECT FEWER.  The three arms were already the
#    same binary with different options; now the arm that represents **the
#    product** is the one **without any option**.  ⛔ Before, to measure the
#    product-with-the-cures, I had to ASK for them: and asking for something is a promise,
#    not a fact.  Now the fact is the binary's default, and the promise
#    is made only by the two off arms — which are the terms of comparison, that is
#    exactly the places where a promise not kept shows at once
#    (they would give three identical arms).
# ⚠ And the check from the log stays identical and MANDATORY all the same: an
#   old binary would be born with the cures off and would give C the numbers of A.
ARMS = [
    ("A", "--clear-threshold-ms 0 --no-adaptive-rate", 0, False,
     "⛔ the two cures switched OFF BY HAND: it is the term of comparison, that is the product "
     "up to 23 August 2026 — and it is remeasured TODAY, on today's binary"),
    ("B", "--clear-threshold-ms 100 --no-adaptive-rate", 100, False,
     "⭐ the QUEUE THRESHOLD ALONE: a stuck delta is abandoned only when the "
     "queue is hopeless for more than 100 ms, not at every frame"),
    ("C", "", 100, True,
     "⭐⭐ THE DEFAULTS since 24 August 2026 (DECISIONS.md §3.1-septies): the "
     "threshold PLUS the rate regulator, and NO option on the command "
     "line — it is the product that ships"),
]

# ⛔ The two lines the product writes at startup, ALWAYS, on and off.
#    They are the contract on which the arm is checked (`LESSONS.md` E1).
RE_THRESHOLD = re.compile(r"video queue threshold \(§5\.1\): (\d+) ms")
RE_RATE_ON = re.compile(r"the rate regulator is ON")
RE_RATE_OFF = re.compile(r"the rate regulator is OFF")


def relaunch(options, wait_threshold, expected_rate):
    """⛔⭐ The server restarts with the arm's options, and THEN the log is
       reread to know what is REALLY in force.

    `LESSONS.md` E1 — «written is not in force».  An old binary
    would refuse `--clear-threshold-ms` and would not start; a right binary with
    a typo in the option would start with the cure OFF and give three identical
    arms, that is «the cure is not needed» on a cure never switched on.
    ⇒ Returns `(ok, righe)`, and `ok` is false if the two lines do not match.
    """
    env = " ".join("%s=%s" % (k, os.environ[k]) for k in
                   ("PORT", "ADDR", "ACCOUNT", "UID_B", "TREE", "WORKDIR",
                    "INSIDE_TREE", "INSIDE_WORK", "UNIT", "MACHINE",
                    "SUDO_PASSWORD"))
    import subprocess
    p = subprocess.run(
        "%s SERVER_OPTIONS=%s bash %s/09-b79-terrain.sh start"
        % (env, json.dumps(options), os.path.join(HERE)),
        shell=True, capture_output=True, timeout=300)
    text = (p.stdout + p.stderr).decode("utf-8", "replace")
    if "server " not in text:
        return False, ["⛔ the server did not start: %s" % text[-300:]]
    # ⛔ The log was emptied by the startup: the startup lines are
    #    the first ones, and we wait for them to be there instead of reading whatever is there.
    lines = []
    for _ in range(30):
        rc, out, _e = root("bash -c \"grep -a 'video queue threshold\\|"
                           "rate regulator' %s/registro.log | head -4\"" % WORKDIR)
        lines = [x for x in out.splitlines() if x.strip()]
        if len(lines) >= 2:
            break
        time.sleep(0.3)
    text_lines = "\n".join(lines)
    m = RE_THRESHOLD.search(text_lines)
    was_read = int(m.group(1)) if m else None
    is_on = bool(RE_RATE_ON.search(text_lines))
    off = bool(RE_RATE_OFF.search(text_lines))
    troubles = []
    if was_read is None:
        troubles.append("the threshold line is not in the log")
    elif was_read != wait_threshold:
        troubles.append("the threshold in force is %d ms, requested %d" % (was_read, wait_threshold))
    if expected_rate and not is_on:
        troubles.append("the rate regulator does NOT appear to be on")
    if (not expected_rate) and not off:
        troubles.append("the rate regulator does NOT appear to be off")
    return (not troubles), (lines + (["⛔ " + g for g in troubles] if troubles else []))


def md5_binary():
    """⚠ The binary I measure must be the one I think, and it is declared."""
    rc, out, _ = root("md5sum %s/src/remotix" % TREE_DIR)
    return out.strip().split()[0] if out.strip() else "?"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREVIOUS SESSION MUST HAVE FINISHED CLOSING — and it is not obvious
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 23 August 2026, found on `07-b64-rete.py` (`log_settled()`, line
# 497) and brought here **without touching that file**: closing a session is
# SLOW when the pacer has a queue — the profile at 10 % loss took
# **29 s more** than the others to write its «final count».  ⇒ Two faults,
# and they have the same root:
#
#  1. **the count read belongs to another run.**  `line0` of the new run is taken
#     BEFORE the line of the old run is written; that line falls inside the
#     window, and `server_counts()` — which takes the LAST one after `line0` — reads
#     it as its own.  `[M]` three profiles in a row reported «sent 4999 ·
#     refused 3 · deferred 7410», which was the count of the FIRST of the three;
#  2. **the slot is still taken.**  Until the old session has
#     closed, §4.4-bis refuses the new one with `FAREWELL 0x0F ALREADY_ACTIVE_REMOTELY`, and
#     the lock lasts until `SILENCE` = 30 s (`09-b78-opening.py` §4).
#     ⇒ A run can fail because of the run BEFORE, and three arms measured in
#       a row stop being comparable.
#
# ⭐⭐ AND IN HERE THE FIRST IS STRUCTURALLY IMPOSSIBLE — it is written because
#     it is a verified fact, not a hope: `07-b64-terreno.sh:106` does
#     `: > "$WORKDIR/registro.log"` at EVERY `turn_on`, and this bench restarts the
#     server at **every arm** (`relaunch()`).  ⇒ In the window of an arm there
#     is no count of the previous arm to steal, and the slot is free because
#     the process holding it is dead.  `[M]` the counter-proof on the 36 runs of
#     23 August: no pair of cells carries identical numbers from the log, and
#     three cells (`loss-3` A, `burst-heavy` A and B) said «NOTHING TO
#     READ» instead of reporting the neighbour's number.
#
# ⛔ What STAYS uncovered, and that is why the two functions are there: inside
#    ONE arm before the run there is the **trigger session**, and its «final
#    count» sits in the same log.  If it arrived late it would fall into the
#    window of the run.  ⇒ We wait for the count to be STILL, and then the run
#    DEMANDS a line of its own.
def count_final_counts():
    rc, out, _ = root("bash -c \"grep -ac 'final count' %s/registro.log "
                      "2>/dev/null || true\"" % WORKDIR)
    t = out.strip()
    return int(t) if t.isdigit() else None


def log_settled(cap=60.0, quiet=3.0):
    """Waits until the count of «final count» lines stays still for `quiet` s.

    Returns that count — it is the `n0` from which the new run demands a line OF ITS OWN — or
    `None` if the log was not read (⛔ and `None` is not zero).
    """
    n = count_final_counts()
    if n is None:
        return None
    stopped, expires = 0.0, time.time() + cap
    while time.time() < expires and stopped < quiet:
        time.sleep(1.0)
        m = count_final_counts()
        if m is None:
            return None
        stopped = (stopped + 1.0) if m == n else 0.0
        n = m
    if stopped < quiet:
        _dub("⚠ in %.0f s the log did not settle: someone is still "
             "closing a session" % cap)
    return n


def count_is_mine(n0, n):
    """⛔ Is the «final count» inside `n["server"]` from THIS run, or not?

    ⇒ If the count of lines has not grown, the line read is from before (at
      worst from the trigger session) and the four server-side numbers **must not be
      judged**.  They are not deleted: they are marked, which is the difference between
      «I did not read» and «nothing happened» (`LESSONS.md` §1.9).
    """
    s = (n or {}).get("server") or {}
    if n0 is None:
        s["conto_dubbio"] = ("⛔ I do not know how many «final count» there were before the "
                             "run: I do not judge the server-side numbers")
        return False
    n1 = count_final_counts()
    if n1 is None or n1 <= n0:
        s["conto_dubbio"] = ("⛔ this run did not write a «final count» OF ITS OWN "
                             "(they were %s, they are %s): the line read is from before — "
                             "I do NOT judge the server-side numbers" % (n0, n1))
        return False
    s["conti_finali"] = [n0, n1]
    return True


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE `quic-net` LINES — which are there in the working tree and not in HEAD
# ═══════════════════════════════════════════════════════════════════════════
def read_quic_network(line0):
    """⭐ `src/webtransport.c:3772` fixes the format as a TEXT CONTRACT:
       prefix `quic-net`, fields `name=valore` without spaces, and `judgement=`
       last, with the value running to the end of the line.  ⇒ `split()` and `split('=',1)`.

    ⛔ It judges nothing: it reduces and prints.  ⚠ `dgram_spurious` = datagrams
       declared lost and then acknowledged = **reordering measured on the
       server side**, and it holds for audio only (streams have no
       per-piece identifier: the price is declared).
    """
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                      "'quic-net ' | tail -400\"" % (line0 + 1, WORKDIR))
    lines = [r for r in out.splitlines() if "quic-net " in r]
    if not lines:
        return {"outcome": "NOTHING TO READ — no «quic-net» line in this run"}
    fields = []
    for r in lines:
        d = {}
        body = r.split("quic-net ", 1)[1]
        judge = None
        if "judgement=" in body:
            body, judge = body.split("judgement=", 1)
        for piece in body.split():
            if "=" in piece:
                k, v = piece.split("=", 1)
                d[k] = v
        d["judgement"] = (judge or "").strip()
        fields.append(d)

    def num(d, k):
        v = d.get(k)
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def listing(k):
        return [x for x in (num(d, k) for d in fields) if x is not None]

    latest = fields[-1]
    judgments = {}
    for d in fields:
        judgments[d["judgement"]] = judgments.get(d["judgement"], 0) + 1
    cwnd = listing("cwnd")
    srtt = listing("srtt_us")
    rttv = listing("rttvar_us")
    n = {"outcome": "letto", "lines": len(fields),
         "persi_tot": num(latest, "lost"),
         "spediti_tot": num(latest, "sent"),
         "cwnd_min": min(cwnd) if cwnd else None,
         "cwnd_mediana": sorted(cwnd)[len(cwnd) // 2] if cwnd else None,
         "cwnd_fine": num(latest, "cwnd"),
         "srtt_us_mediana": sorted(srtt)[len(srtt) // 2] if srtt else None,
         "srtt_us_max": max(srtt) if srtt else None,
         "rttvar_us_mediana": sorted(rttv)[len(rttv) // 2] if rttv else None,
         "pto_us_fine": num(latest, "pto_us"),
         "dgram_lost": num(latest, "dgram_lost"),
         "dgram_spurious": num(latest, "dgram_spurious"),
         "dgram_ok": num(latest, "dgram_ok"),
         "judgments": judgments}
    return n


def print_quic_network(n):
    if n.get("outcome") != "letto":
        _dub("QUIC    %s" % n.get("outcome"))
        return
    _inf("QUIC    %d lines · lost %s packets out of %s sent · cwnd min %s / "
         "median %s / end %s"
         % (n["lines"], n["persi_tot"], n["spediti_tot"], n["cwnd_min"],
            n["cwnd_mediana"], n["cwnd_fine"]))
    _inf("        srtt median %s us (max %s) · rttvar median %s us · final "
         "pto %s us"
         % (n["srtt_us_mediana"], n["srtt_us_max"], n["rttvar_us_mediana"],
            n["pto_us_fine"]))
    _inf("        datagrams (audio): lost %s · acknowledged %s · ⭐ FALSE "
         "%s (= reordering measured by the server)"
         % (n["dgram_lost"], n["dgram_ok"], n["dgram_spurious"]))
    _inf("        server judgements: %s"
         % json.dumps(n["judgments"], ensure_ascii=False))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREDICATES OF THE PAIR — written FIRST
# ═══════════════════════════════════════════════════════════════════════════
#
# ── the thresholds, in one place only, and each with its reason ────────────
MAX_KEY_QUOTA = 0.10   # ⛔ the complement of `QUOTA_DELTA = 0.90` of 09-b70,
                          #    that is §3.3 read backwards.  It is not a new
                          #    threshold: it is the same, and two thresholds for the same
                          #    fact are two thresholds that diverge.
NOISE = 0.05             # ⚠ 09-b70 estimates at 5 % the difference between two runs
                          #    of the same machine
MIN_DIFFERENCE = 0.10  # ⛔ TWICE the noise: below it, this bench does not
                          #    judge instead of calling the noise an «effect»
DRIFT_TOLERATED_MS = 100.0  # ⭐ = the threshold itself: the cure keeps a delta
                             #   until the queue is hopeless for more
                             #   than N ms, so the delay it can add
                             #   is N by construction


def _quota_keys(n):
    if not B70._has_measured(n):
        return None
    return round(1.0 - n["quota_delta"], 4)


def p_spiral_off(a, x, label):
    """**K′ — THE CURE SWITCHES OFF THE SPIRAL.**

    ⛔ And it is SILENT where the spiral was not there in A: putting out a fire that is not there
       is not a merit, and it is a green that would award itself.
    """
    if not B70._has_measured(a):
        return _mute("arm A did not measure: without it there is no "
                     "pair, and a number without a denominator does not judge")
    if not B70._has_measured(x):
        return _mute("arm %s did not measure: %s"
                     % (label, x.get("outcome", "?")))
    qa, qx = _quota_keys(a), _quota_keys(x)
    queue = ("keyframes %d out of %d = %.1f %% in arm %s, against %d out of %d = "
            "%.1f %% in A" % (x["keys"], x["frames"], qx * 100, label,
                              a["keys"], a["frames"], qa * 100))
    if qa <= MAX_KEY_QUOTA:
        return _mute("in A the spiral was NOT there (%.1f %% keyframes, below "
                     "%.0f %%): there is nothing to switch off, and a green here I "
                     "would award myself — %s"
                     % (qa * 100, MAX_KEY_QUOTA * 100, queue))
    if qx <= MAX_KEY_QUOTA:
        return _si("⭐ THE SPIRAL HAS SWITCHED OFF: %s" % queue)
    return _no("⛔ the spiral did NOT switch off: %s" % queue)


def p_rate_restored(a, x, label):
    """**F′ — THE CURE GIVES BACK RHYTHM**, and the threshold is twice the noise.

    ⚠ Three outcomes, not two: below a 10 % difference this bench says
      «indistinguishable» instead of calling the noise an effect.
    """
    if not B70._has_measured(a) or not B70._has_measured(x):
        return _mute("one of the two arms did not measure: A «%s», %s «%s»"
                     % (a.get("outcome", "?"), label, x.get("outcome", "?")))
    if not a["fps"]:
        return _mute("arm A has zero frames/s: there is no ratio")
    r = x["fps"] / a["fps"]
    queue = ("%.2f/s in arm %s against %.2f/s in A (%.0f %%) · worst "
            "second %s against %s · ⚠ AND THE PRICE: final drift %s ms against "
            "%s ms (maximum %s against %s)"
            % (x["fps"], label, a["fps"], r * 100, x["fps_finestra_min"],
               a["fps_finestra_min"], x["deriva_fine_ms"], a["deriva_fine_ms"],
               x["deriva_max_ms"], a["deriva_max_ms"]))
    if r >= 1.0 + MIN_DIFFERENCE:
        return _si("⭐ the rhythm has come back: %s" % queue)
    if r <= 1.0 - MIN_DIFFERENCE:
        return _no("⛔ THE CURE TAKES RHYTHM AWAY instead of giving it: %s" % queue)
    return _mute("indistinguishable from noise (less than %.0f %%, which is "
                 "twice the %.0f %% between two runs of the same machine): %s"
                 % (MIN_DIFFERENCE * 100, NOISE * 100, queue))


def p_healthy_line(arms):
    """**S′ — THE CURE DOES NOT COST ON THE HEALTHY LINE**, and it is worth more than all the
       others put together.

    ⛔ On `delay-30` there is nothing to cure: zero loss, zero reordering,
       only thirty milliseconds of delay.  ⇒ The three arms must be
       indistinguishable, and if they are not it is the most important discovery of the
       run — because it would mean the cure is paid for even where it is not needed.

    `bracci` = {"A": n, "B": n, "C": n}
    """
    a = arms.get("A") or {}
    if not B70._has_measured(a):
        return _mute("arm A of the healthy line did not measure: %s"
                     % a.get("outcome", "?"))
    troubles, said = [], []
    for et in ("B", "C"):
        x = arms.get(et) or {}
        if not B70._has_measured(x):
            return _mute("arm %s of the healthy line did not measure: %s"
                         % (et, x.get("outcome", "?")))
        r = x["fps"] / a["fps"] if a["fps"] else 0.0
        dq = _quota_keys(x)
        dd = x["deriva_fine_ms"] - a["deriva_fine_ms"]
        said.append("%s %.2f/s (%.0f %%), keyframes %.1f %%, drift %s ms "
                     "(%+.0f against A)"
                     % (et, x["fps"], r * 100, dq * 100, x["deriva_fine_ms"], dd))
        if abs(r - 1.0) > NOISE:
            troubles.append("%s: %.2f/s against %.2f/s = %.0f %%, beyond the %.0f %% "
                        "of noise" % (et, x["fps"], a["fps"], r * 100,
                                       NOISE * 100))
        if dq > MAX_KEY_QUOTA:
            troubles.append("%s: %.1f %% keyframes on a line that loses "
                        "nothing" % (et, dq * 100))
        if dd > DRIFT_TOLERATED_MS:
            troubles.append("%s: the final drift grows by %.0f ms, more than the "
                        "threshold itself (%.0f ms) — it is not the threshold "
                        "at work" % (et, dd, DRIFT_TOLERATED_MS))
    queue = "A %.2f/s, keyframes %.1f %%, drift %s ms · %s" % (
        a["fps"], _quota_keys(a) * 100, a["deriva_fine_ms"], " · ".join(said))
    if troubles:
        return _no("⛔⛔ THE CURE COSTS ON THE HEALTHY LINE — %s · %s"
                   % (" · ".join(troubles), queue))
    return _si("the three arms are indistinguishable on the healthy line: %s" % queue)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PLAN.md` §0.3.4: *«a bench that cannot see the defect it looks for has no
#    right to green»*.  Here pairs are built and we check that the three
#    predicates give what is written FIRST — green, red **and mute**.
def _g(fps, key_every=0, drift=0.0, seconds=25):
    """A fake run, reduced by the SAME `measure()` that runs on the real runs."""
    return B76._make_round(fps, seconds=seconds, key_every=key_every,
                         drift=drift)


def certify():
    print("⭐ CERTIFICATION OF THE TWO-CURES BENCH — the expected outcome is written "
          "FIRST\n")
    print("   ⛔ No contact with the test machine: here the TOOL is tested,"
          "\n      not the product.\n")
    do_import(with_network=False)
    green = True

    def outcome(name, seen, expected, why):
        nonlocal green
        all_ok = (seen is expected)
        green = green and all_ok
        print("  %s%-64s atteso %-5s visto %-5s\n        %s"
              % ("OK  " if all_ok else "⛔  ", name, expected, seen, why[:170]))

    # ── 1 · K′ · does the spiral switch off? ───────────────────────────────
    print("  ── K′ · the cure switches off the spiral ──\n")
    # ⭐ `key_every=1` = all frames are keyframes: it is the face of the
    #    defect of 21 August (144 keyframes out of 144).
    spiral = _g(10, key_every=1)
    sana = _g(40)
    p, q = p_spiral_off(spiral, sana, "B")
    outcome("1-⭐ A is all keyframes, B has none: the spiral has switched off",
          p, True, q)

    p, q = p_spiral_off(spiral, _g(12, key_every=1), "B")
    outcome("2-⛔⛔ A is all keyframes and so is B: the cure switched off nothing",
          p, False, q)

    p, q = p_spiral_off(sana, _g(41), "B")
    outcome("3-⭐⭐ in A the spiral was NOT there: the bench is SILENT instead of taking "
          "a green it would award itself", p, None, q)

    p, q = p_spiral_off(B70.measure([], 25, None, None), sana, "B")
    outcome("4-⛔ arm A did not measure: without a denominator, it is SILENT",
          p, None, q)

    # ── 2 · F′ · does the rhythm come back? and below the noise it is SILENT ─
    print("\n  ── F′ · the cure gives back rhythm (and noise is not an "
          "effect) ──\n")
    p, q = p_rate_restored(_g(10), _g(40), "B")
    outcome("5-⭐ from 10/s to 40/s: the rhythm has come back", p, True, q)

    p, q = p_rate_restored(_g(40), _g(41), "B")
    outcome("6-⭐⭐ 40 against 41: it is 2.5 %, less than twice the noise — the "
          "bench does NOT call the noise an effect and is SILENT", p, None, q)

    p, q = p_rate_restored(_g(40), _g(20), "C")
    outcome("7-⛔⛔ THE CURE TAKES RHYTHM AWAY: 40/s in A and 20/s in C — and it is the "
          "most important discovery that could come out of here", p, False, q)

    # ⚠⚠ THE BOUNDARY, and it must be tested from BOTH sides — a three-outcome
    #    predicate goes wrong right there in the middle.  ⛔ And the first expectation I had
    #    written was WRONG: I had taken as «above the boundary» a 44 against
    #    40, which the builder renders as 44.04 against 40.04 = **109.99 %**, that is
    #    a hair BELOW.  ⇒ The case was not fixed by moving the threshold:
    #    the EXPECTATION was fixed, which was mine and not the predicate's.
    p, q = p_rate_restored(_g(40), _g(44), "B")
    outcome("8-⚠ a hair BELOW the boundary (109.99 %): the bench is silent",
          p, None, q)

    p, q = p_rate_restored(_g(40), _g(45), "B")
    outcome("9-⚠ one step ABOVE the boundary (112.5 %): the bench judges",
          p, True, q)

    # ── 3 · S′ · ⛔ the healthy line, worth more than all the others ───────
    print("\n  ── ⛔⛔ S′ · the cure must not cost on the healthy line ──\n")
    p, q = p_healthy_line({"A": _g(40), "B": _g(40.5), "C": _g(39.6)})
    outcome("10-⭐ the three arms within 5 %: indistinguishable", p, True, q)

    p, q = p_healthy_line({"A": _g(40), "B": _g(40.2), "C": _g(34)})
    outcome("11-⛔⛔ THE DEFECT THIS PREDICATE EXISTS TO FIND: C loses "
          "15 % on the HEALTHY line", p, False, q)

    p, q = p_healthy_line({"A": _g(40), "B": _g(40, key_every=1), "C": _g(40)})
    outcome("12-⛔⛔ B is all keyframes on a line that loses nothing: the cure "
          "SWITCHED ON a spiral where there was none", p, False, q)

    # ⭐ The price, and it is the case the mandate asks not to confuse with an
    #   improvement: same rhythm, but the delay grows more than the threshold.
    p, q = p_healthy_line({"A": _g(40), "B": _g(40, drift=0.0),
                         "C": _g(40, drift=0.5)})
    outcome("13-⛔⭐ THE PRICE: C keeps the rhythm but the drift grows more than the "
          "threshold itself (100 ms) — it is not the threshold at work", p, False, q)

    p, q = p_healthy_line({"A": _g(40), "B": _g(40),
                         "C": B70.measure([], 25, None, None)})
    outcome("14-⛔ one arm of the healthy line did not measure: SILENT", p, None, q)

    # ── 4 · ⛔ the arm is checked from the LOG, not from the command line ───
    print("\n  ── ⛔ «written is not in force»: the two startup lines ──\n")
    # ⚠ Here the machine is not touched: the RECOGNISER is exercised on the real
    #   lines the product writes (`clear_out_declare`, `wt_adaptive_rate`).
    # ⛔ Updated on 10 Oct 2026 to the lines the product writes NOW, in English
    #    (`clear_out_declare()` and `wt_adaptive_rate()` in `src/webtransport.c`).
    #    ⚠ They are not made up: they are the product's text, shortened at the tail.
    real_A = ("⛔ PHASE 9, video queue threshold (§5.1): 0 ms — OFF: "
              "it abandons at every more recent frame, that is the "
              "product up to 23 Aug 2026 byte for byte.  ⚠ And it is NOT "
              "the default: since 24 August it is born ON at 100 ms, so "
              "someone typed `--clear-threshold-ms 0` on purpose.\n"
              "⛔ the rate regulator is OFF by whoever launched the "
              "server (`--no-adaptive-rate`): no frame "
              "will ever be skipped because of the line")
    real_C = ("⭐ PHASE 9, video queue threshold (§5.1): 100 ms — "
              "ON: above the threshold a stuck delta is abandoned, below "
              "it is KEPT.  ⭐ It is the DEFAULT since 24 Aug 2026\n"
              "⭐ PHASE 9: the rate regulator is ON — a frame "
              "does NOT leave when 2 deltas in flight still have bytes in my "
              "output queue.  ⭐ It is the DEFAULT since 24 Aug 2026")

    def recognize(text, threshold, rate):
        m = RE_THRESHOLD.search(text)
        was_read = int(m.group(1)) if m else None
        is_on = bool(RE_RATE_ON.search(text))
        off = bool(RE_RATE_OFF.search(text))
        if was_read != threshold:
            return False, "the threshold in force is %s, requested %s" % (was_read, threshold)
        if rate and not is_on:
            return False, "the regulator does not appear to be on"
        if (not rate) and not off:
            return False, "the regulator does not appear to be off"
        return True, "threshold %s ms, regulator %s" % (was_read,
                                                       "on" if rate else "off")

    p, q = recognize(real_A, 0, False)
    outcome("15-⭐ arm A recognised from the product's real lines", p, True, q)
    p, q = recognize(real_C, 100, True)
    outcome("16-⭐ arm C recognised from the product's real lines", p, True, q)
    p, q = recognize(real_A, 100, False)
    outcome("17-⛔⛔ threshold 100 REQUESTED and 0 in force: the bench STOPS "
          "instead of measuring three identical arms and concluding «the cure is not "
          "needed»", p, False, q)
    p, q = recognize(real_C, 100, False)
    outcome("18-⛔ the regulator requested OFF and it appears on", p, False, q)

    # ── 5 · the reduction of the `quic-net` lines, which is a text contract ─
    print("\n  ── ⭐ the `quic-net` lines: the text contract ──\n")
    fake = [
        "12:00:01.000 wt      quic-net 192.168.0.2:52344 since_ms=0 lost=0 "
        "lost_d=0 cwnd=14000 cwnd_left=14000 srtt_us=30100 rttvar_us=900 "
        "pto_us=132000 sent=100 dgram_lost=0 dgram_ok=10 dgram_spurious=0 "
        "judgement=-- nothing to report",
        "12:00:02.000 wt      quic-net 192.168.0.2:52344 since_ms=1000 lost=7 "
        "lost_d=7 cwnd=6000 cwnd_left=0 srtt_us=41230 rttvar_us=11400 "
        "pto_us=132000 sent=210 dgram_lost=5 dgram_ok=40 dgram_spurious=3 "
        "judgement=⛔ the line is losing",
    ]
    saved = globals().get("root")
    globals()["root"] = lambda c, cap=300: (0, "\n".join(fake), "")
    n = read_quic_network(0)
    globals()["root"] = saved
    outcome("19-⭐ two lines reduced: lost 7, cwnd min 6000, ⭐ dgram_spurious 3 "
          "(= reordering seen by the server)",
          (n["lines"] == 2 and n["persi_tot"] == 7 and n["cwnd_min"] == 6000
           and n["dgram_spurious"] == 3 and n["srtt_us_max"] == 41230),
          True, json.dumps({k: n[k] for k in ("lines", "persi_tot", "cwnd_min",
                                              "dgram_spurious", "srtt_us_max")}))
    outcome("20-⭐ and `judgement=` runs to the end of the line, spaces included",
          (n["judgments"].get("⛔ the line is losing") == 1
           and n["judgments"].get("-- nothing to report") == 1),
          True, json.dumps(n["judgments"], ensure_ascii=False))

    saved = globals().get("root")
    globals()["root"] = lambda c, cap=300: (0, "", "")
    n = read_quic_network(0)
    globals()["root"] = saved
    outcome("21-⛔ no `quic-net` line: «I did not read» is not «zero» "
          "(`CODER.md` §3.10)", n.get("outcome") != "letto", True, n.get("outcome"))

    print("\n== %s" % ("⭐ THE BENCH CAN SEE THE DEFECTS IT LOOKS FOR — and can stay SILENT "
                       "where it cannot judge"
                       if green else
                       "⛔⛔ THE BENCH CANNOT SEE WHAT IT LOOKS FOR: none of its greens "
                       "is to be believed"))
    return 0 if green else 1


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def neighbors_not_mine():
    """⚠ `LESSONS.md` §1.26: two benches on the same machine do not give a
       red, they give **a plausible number**.  ⛔ The 7930 of `09-b76` was left
       on: it is not mine and it is not switched off, but if someone attached to it my
       numbers would be dirty.  ⇒ We count who is ATTACHED, not who
       listens: a server on and idle is not a running bench."""
    report = {}
    for p in ("7900", "7910", "7920", "7930", "7932", "7730"):
        rc, out, _ = root("bash -c \"ss -uan 2>/dev/null | grep ':%s ' | "
                          "grep -vc UNCONN || true\"" % p)
        report[p] = out.strip()
    rc, out, _ = root("uptime")
    report["load"] = out.strip()[-32:]
    return report


def profile(name):
    for p in B76.PROFILES:
        if p[0] == name:
            return p
    return None


def install_profile(rules):
    """⛔ `del root` + `add`, never `change`: `[M]` 23 Aug 2026, `tc qdisc change`
       is STICKY and dragged a `reorder` along for four profiles
       — which would have measured a network nobody had asked for."""
    ok, q = NETWORK.tighten(B76._rules(rules))
    if not ok:
        return False, q, ""
    B76.probe_filters()
    reread = B76.rule_reread()
    passes, why = B76.check_rule(rules, reread)
    return passes, why, reread


def one_cell(profile_name, rules, verify, label, options, threshold,
                rate, seconds):
    """One arm of a profile: the sequence of the seven steps of the header."""
    entry = {"profile": profile_name, "braccio": label, "options": options}

    # 1 · the network is put back smooth, so the trigger session is born clean
    NETWORK.restore(report_it=False)
    # 2 · the server restarts with the arm, and the arm is CHECKED
    ok, lines = relaunch(options, threshold, rate)
    entry["startup"] = lines
    for r in lines:
        _inf("AVVIO   %s" % r.split("startup   ")[-1][:150])
    if not ok:
        _ko("⛔ arm %s is NOT in force: I do not measure this cell"
            % label)
        entry["outcome"] = "THE ARM IS NOT IN FORCE"
        return entry
    # 3 · the trigger session, ON A CLEAN NETWORK (see the header, point 3)
    if not B70.trigger_session():
        _ko("the trigger session does not open: I do not measure this cell")
        entry["outcome"] = "THE TRIGGER SESSION DOES NOT OPEN"
        return entry
    # 4 · the profile, and it is reread
    pass_r, why_r, reread = install_profile(rules)
    entry["regola_riletta"] = reread
    (_ok if pass_r else _ko)("the rule: %s" % why_r)
    if not pass_r:
        entry["outcome"] = "THE INSTALLED RULE IS NOT THE ONE REQUESTED"
        return entry
    # 5 · the probe: was the fault put in?  ⛔ and it is redone at every arm
    s = B76.run_probe()
    B76.print_probe(s)
    pass_g, why_g = B76.p_fault_set(profile_name, verify, s)
    (_ok if pass_g else (_dub if pass_g is None else _ko))(
        "THE FAULT WAS PUT IN: %s" % why_g)
    entry["probe"] = s
    entry["fault"] = {"passes": pass_g, "why": why_g}
    # 6 · the run
    usc = B76.scene_turn_on("barra")
    if not usc:
        _ko("the scene does not start: I do NOT judge this cell")
        entry["outcome"] = "THE SCENE DID NOT START"
        return entry
    before = B76.qdisc_counts()
    # ⛔ The trigger session must have FINISHED closing, or its «final
    #    count» falls into the window of this run (⇒ `log_settled`).
    n0 = log_settled()
    line0 = B76.log_line_list()
    n = B70.cur_round("%s-%s" % (profile_name, label), "barra",
                 B70.FULL_CANVAS, seconds)
    if not count_is_mine(n0, n):
        _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
    B76.scene_turn_off()
    after = B76.qdisc_counts()
    # 7 · the counters around the run and the `quic-net` lines
    delta = {k: after[k] - before[k] for k in before} if (before and after) else None
    entry["qdisc"] = delta
    quic = read_quic_network(line0)
    entry["quic"] = quic
    B70.print_round(n)
    # ⛔⭐ THE SAFETY NET OF `09-b70` IS USED, NOT BYPASSED: it is the predicate
    #    that refuses to say anything about the server side when the log is not
    #    from this run — that is the only thing that would have caught by itself the
    #    defect of the badly wrapped `root`.
    # ⚠ And we declare what it protects: K′ and F′ do NOT go through here (they live on the
    #   client's §11.1 trace), so a red of its own does not touch the verdict —
    #   it marks as not judgeable the four CORROBORATION numbers
    #   (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`, `abandoned`).
    if hasattr(B70, "p_log_read"):
        pr, why_pr = B70.p_log_read(n)
        (_ok if pr else (_dub if pr is None else _ko))(
            "the log is from THIS run (§1.9): %s" % why_pr)
        entry["registro_letto"] = {"passes": pr, "why": why_pr}
    _inf("QDISC   around the run: %s" % json.dumps(delta))
    print_quic_network(quic)
    # ⛔ The lock of §8.2: if the slot was taken, this cell is not
    #    a measurement of the cure — it is a measurement of thirty seconds of lock.
    queue = LAST_CLIENT["text"] or (n.get("coda_cliente") or "")
    if "GIA_ATTIVA" in queue or "0x0f" in queue.lower():
        _dub("⚠ the client found the slot TAKEN (§8.2 reason 0x0F): "
             "this cell does not measure the cure")
        entry["outcome"] = "IL POSTO ERA OCCUPATO"
    entry["round"] = n
    entry["staccato_dal_cliente"] = ("I did NOT stay attached" in queue)
    return entry


def pair_up(a):
    _log("09-b79 · THE TWO CURES PAIRED — port %d · dev «%s»" % (PORT, DEV))
    print("   ⛔ «%s» (ssh + the user's session) is NOT touched" % VIETATA)
    print("   ⛔ 7900/7910/7920/7930/7932 belong to others: they are COUNTED, not touched")
    md5 = md5_binary()
    print("   ⭐ the binary I measure: md5 %s (working tree, not HEAD)" % md5)
    print("   --  «%s» before: %s" % (DEV, NETWORK.qdisc() or "(none)"))

    if not B76.ship_probe():
        _ko("the scripts were not written in %s" % WORKDIR)
        return 2
    if B76.choose_probe_port() is None:
        _ko("⛔ none of my probe ports is free: I do NOT measure, "
            "because without the probe I do not know whether the fault was put in")
        return 2
    _ok("the probe and the reader are in %s · the probe will use port %d"
        % (WORKDIR, B76.PROBE_PORT))
    before_neighbors = neighbors_not_mine()
    _inf("attached to the ports NOT mine, BEFORE: %s"
         % json.dumps(before_neighbors, ensure_ascii=False))

    names = [x.strip() for x in a.profiles.split(",") if x.strip()]
    if a.only:
        names = [n for n in names if a.only in n]
    chosen = []
    for name in names:
        p = profile(name)
        if not p:
            _ko("the profile «%s» does not exist in 09-b76" % name)
            return 2
        chosen.append(p)
    if not chosen:
        _ko("no profile chosen")
        return 2
    arms = [b for b in ARMS if b[0] in a.arms]
    _inf("%d profiles × %d arms = %d cells of %d s"
         % (len(chosen), len(arms), len(chosen) * len(arms), a.seconds))

    CHI = "09-b79"
    LEASE = 900
    try:
        LUC.take(CHI, seconds=LEASE, wait=a.wait)
    except Exception as e:
        _ko("⛔ I DO NOT MEASURE: %s" % e)
        return 2
    expiry = time.time() + LEASE

    outcomes = []
    NETWORK.guardian_arm(min(7200, len(chosen) * len(arms) * (a.seconds + 90) + 900))
    try:
        for p in chosen:
            name, rules, _full, _spir, _without, why, verify = p
            if time.time() > expiry - 400:
                if B76.renew(CHI, LEASE):
                    expiry = time.time() + LEASE
                    _inf("⛔ lock lease renewed for %d s" % LEASE)
                else:
                    _ko("⛔ the lock is no longer mine: I STOP")
                    break
            _log("PROFILE «%s» — %s" % (name, why[:110]))
            cell = {}
            for label, options, threshold, rate, why_b in arms:
                _log("  %s · arm %s — %s" % (name, label, why_b[:100]))
                v = one_cell(name, rules, verify, label, options,
                                threshold, rate, a.seconds)
                outcomes.append(v)
                cell[label] = v.get("round") or {"outcome": v.get("outcome", "?")}

            # ── the predicates of the PAIR, and each one says its why ────────
            _log("  %s · THE PAIR" % name)
            A = cell.get("A") or {}
            for et in ("B", "C"):
                if et not in cell:
                    continue
                passes, q = p_spiral_off(A, cell[et], et)
                (_ok if passes else (_dub if passes is None else _ko))(
                    "K′ · the cure switches off the spiral (%s): %s" % (et, q))
                pass2, q2 = p_rate_restored(A, cell[et], et)
                (_ok if pass2 else (_dub if pass2 is None else _ko))(
                    "F′ · the cure gives back rhythm (%s): %s" % (et, q2))
                outcomes.append({"profile": name, "coppia": et,
                              "K": {"passes": passes, "why": q},
                              "F": {"passes": pass2, "why": q2}})
            if name == "delay-30" and len(cell) == 3:
                passes, q = p_healthy_line(cell)
                (_ok if passes else (_dub if passes is None else _ko))(
                    "⛔⛔ S′ · the cure must NOT cost on the healthy line: %s" % q)
                outcomes.append({"profile": name, "linea_sana":
                              {"passes": passes, "why": q}})
    finally:
        B76.scene_turn_off()
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        restored = NETWORK.restore()
        LUC.release(CHI)

    os.makedirs(OUT, exist_ok=True)
    dove = os.path.join(OUT, "09-b79-esiti.json")
    with open(dove, "w") as f:
        json.dump({"md5_binario": md5, "outcomes": outcomes,
                   "vicini_prima": before_neighbors,
                   "vicini_dopo": neighbors_not_mine()}, f,
                  ensure_ascii=False, indent=1)
    _inf("outcomes in %s" % dove)
    after_neighbors = neighbors_not_mine()
    _inf("attached to the ports NOT mine, AFTER: %s"
         % json.dumps(after_neighbors, ensure_ascii=False))
    table(outcomes)
    rossi = [e for e in outcomes
             if any((e.get(k) or {}).get("passes") is False
                    for k in ("K", "F", "linea_sana"))]
    if not restored:
        _ko("⛔ the network did NOT go back as it was: put it back by hand with «restore»")
        return 2
    return 1 if rossi else 0


def table(outcomes):
    """⛔ §6.2: ALL the quantities are printed.  ⭐ And the DRIFT sits next to the
       frames/s on every line, because a cure that doubles the rhythm and
       triples the delay is not obviously an improvement — and it is a
       choice that belongs to the user, not to this bench."""
    _log("THE THREE-ARM TABLE — ⚠ and the price (the drift) sits next to the "
         "gain")
    print("  %-14s %-2s %7s %7s %7s %7s %8s %8s %9s"
          % ("profile", "ar", "fps", "worst", "keyfr%", "drift", "driftMx",
             "Mbit/s", "cwnd_min"))
    for e in outcomes:
        n = e.get("round")
        if not n:
            continue
        if not B70._has_measured(n):
            print("  %-14s %-2s   %s" % (e["profile"], e["braccio"],
                                         (n.get("outcome") or "?")[:70]))
            continue
        q = e.get("quic") or {}
        print("  %-14s %-2s %7.2f %7s %6.1f%% %7s %8s %8s %9s"
              % (e["profile"], e["braccio"], n["fps"], n["fps_finestra_min"],
                 (1 - n["quota_delta"]) * 100, n["deriva_fine_ms"],
                 n["deriva_max_ms"], n["mbit_s_filo"], q.get("cwnd_min")))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE `detach` STEP — «WHO» detached on `burst-heavy`
# ═══════════════════════════════════════════════════════════════════════════
def detach(a):
    """⛔ It does not deduce: it asks four independent witnesses (see
       the header).  ⚠ And the third possibility — «it never opened» —
       is ruled out EXPLICITLY, because it looks the same as detaching."""
    _log("09-b79 · `burst-heavy` — ⛔ WHO DETACHED?")
    p = profile("burst-heavy")
    md5 = md5_binary()
    print("   ⭐ binary md5 %s · netem profile: %s" % (md5, " ".join(p[1])))

    # ⭐ The first witness is read in the SOURCE, before running: `IDLE_MS`.
    rc, out, _ = root("bash -c \"grep -n 'IDLE_MS' %s/src/transport.c | head -4\""
                      % TREE_DIR)
    _inf("`[R]` src/transport.c: %s" % " | ".join(out.split()))

    if not B76.ship_probe() or B76.choose_probe_port() is None:
        _ko("the scripts or the probe port are missing")
        return 2

    CHI = "09-b79-stacco"
    try:
        LUC.take(CHI, seconds=900, wait=a.wait)
    except Exception as e:
        _ko("⛔ I DO NOT MEASURE: %s" % e)
        return 2
    NETWORK.guardian_arm(1800)
    report = {}
    try:
        NETWORK.restore(report_it=False)
        ok, lines = relaunch("", 0, False)
        if not ok:
            _ko("arm A is not in force: %s" % lines)
            return 2
        if not B70.trigger_session():
            _ko("the trigger session does not open (on a CLEAN network)")
            return 2
        _ok("⭐ on a CLEAN network the session opens: what follows belongs to the fault")
        pass_r, why_r, reread = install_profile(p[1])
        (_ok if pass_r else _ko)("the rule: %s" % why_r)
        if not pass_r:
            return 2
        s = B76.run_probe()
        B76.print_probe(s)
        pass_g, why_g = B76.p_fault_set("burst-heavy", p[6], s)
        (_ok if pass_g else (_dub if pass_g is None else _ko))(
            "THE FAULT WAS PUT IN: %s" % why_g)
        report["probe"] = s

        usc = B76.scene_turn_on("barra")
        if not usc:
            _ko("the scene does not start")
            return 2
        n0 = log_settled()      # ⛔ see `log_settled`
        line0 = B76.log_line_list()
        t0 = time.time()
        n = B70.cur_round("stacco-raffica-forte", "barra", B70.FULL_CANVAS, a.seconds)
        if not count_is_mine(n0, n):
            _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
        B76.scene_turn_off()
        B70.print_round(n)
        report["round"] = n
        report["quic"] = read_quic_network(line0)
        print_quic_network(report["quic"])

        # ── WITNESS 1 · THE CLIENT, which says it by itself ────────────────
        _log("WITNESS 1 · the client (`01-b3-client.py:1979`)")
        queue = LAST_CLIENT["text"] or (n.get("coda_cliente") or "")
        print("   ┌─ the client, IN FULL (⛔ not its last 400 bytes) ─")
        for r in queue.splitlines():
            if r.strip() and "tput:" not in r:
                print("   │ %s" % r[:160])
        print("   └─")
        attached = "still attached after" in queue
        detached = "I did NOT stay attached" in queue
        report["cliente"] = {"attaccato_fino_in_fondo": attached,
                            "detached": detached, "queue": queue}
        if attached:
            _ok("⭐⭐ THE CLIENT SAYS THE SESSION DID **NOT** DETACH: it "
                "stayed attached for all the %d s requested" % a.seconds)
        elif detached:
            _ko("⛔ the client says it dropped — and it also says why")
        else:
            _dub("the client said neither one thing nor the other")

        # ── WITNESS 2 · THE SERVER LOG ─────────────────────────────────────
        _log("WITNESS 2 · the server log — the farewell reasons")
        searched = ("farewell reason=", "the client takes its farewell", "slot DENIED",
                   "BANNED", "SILENZIO", "final count", "closing",
                   "GIA_ATTIVA", "idle", "expired")
        report["log"] = {}
        for c in searched:
            rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                              "-i '%s' | tail -3\"" % (line0 + 1, WORKDIR, c))
            lines = [x[:200] for x in out.splitlines() if x.strip()]
            report["log"][c] = lines
            if lines:
                for r in lines:
                    _inf("«%s» → %s" % (c, r))
        if not any(report["log"][c] for c in
                   ("farewell reason=", "the client takes its farewell", "slot DENIED",
                    "BANNED", "GIA_ATTIVA")):
            _ok("⭐ NO farewell, NO slot denied, NO ban in the whole "
                "run: on the server side nobody detached")

        # ── WITNESS 3 · THE HANDSHAKE — the third possibility ──────────────
        _log("WITNESS 3 · ⚠ «it never opened» looks the same as "
             "«it detached»")
        is_open = "SESSION" in queue or (n.get("fotogrammi_grezzi") or 0) > 0
        rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                          "'ADMITTED\\|ATTACH\\|session open\\|monitor «' | "
                          "head -5\"" % (line0 + 1, WORKDIR))
        for r in out.splitlines()[:5]:
            _inf("opening: %s" % r[:180])
        report["apertura"] = {"is_open": is_open, "lines": out.splitlines()[:5]}
        if is_open:
            _ok("⭐ THE SESSION OPENED (the hypothesis «the handshake does not "
                "complete» is ruled out): `09-b78-opening.py` had already "
                "measured it up to 25 %% loss, 10 runs out of 10 in ~1.3 s")
        else:
            _ko("⛔ the session NEVER opened: it is not a detach")

        # ── WITNESS 4 · THE WINDOW, and the server's count ─────────────────
        _log("WITNESS 4 · the congestion window and the server counts")
        srv = (n.get("server") or {})
        _inf("SERVER  %s" % json.dumps(srv, ensure_ascii=False)[:600])
        q = report["quic"]
        if q.get("outcome") == "letto":
            _inf("⭐ the window: cwnd min %s, median %s, end %s · judgements %s"
                 % (q["cwnd_min"], q["cwnd_mediana"], q["cwnd_fine"],
                    json.dumps(q["judgments"], ensure_ascii=False)))
        report["secondi_veri"] = round(time.time() - t0, 1)
    finally:
        B76.scene_turn_off()
        NETWORK.restore()
        LUC.release(CHI)

    os.makedirs(OUT, exist_ok=True)
    dove = os.path.join(OUT, "09-b79-stacco.json")
    with open(dove, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    _inf("outcomes in %s" % dove)

    # ── THE VERDICT, and the right word ────────────────────────────────────
    _log("THE VERDICT on `burst-heavy`")
    n = report.get("round") or {}
    if report.get("cliente", {}).get("attaccato_fino_in_fondo"):
        _ok("⭐⭐⭐ NOBODY DETACHED.  The connection stayed alive for "
            "all the %d s; what stopped was the DELIVERY OF FRAMES after "
            "%s s.  ⇒ The red of `09-b76` is true as a number and WRONG as a "
            "word: `p_nothing_detach` measures how long delivery lasted, not "
            "whether the connection dropped.  ⛔ And the fact stays serious — a "
            "session alive and MUTE is a frozen screen — but it has another name and "
            "another cause." % (a.seconds, n.get("vissuto_s")))
        return 0
    if report.get("cliente", {}).get("staccato"):
        _ko("⛔ THE CLIENT DROPPED: %s" % report["cliente"]["coda"][-300:])
        return 1
    _dub("none of the witnesses answered: I have nothing to judge")
    return 3


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("step", nargs="?",
                   choices=["terrain", "pair", "detach", "restore", "status"])
    p.add_argument("--certify", action="store_true",
                   help="⭐ the positive control: it does not touch the machine")
    p.add_argument("--seconds", type=int, default=25)
    p.add_argument("--only", default="", help="one profile only, by name")
    p.add_argument("--arms", default="ABC")
    p.add_argument("--profiles", default=("delay-30,loss-1,loss-3,"
                                         "jitter-15,jitter-30,bad-home,"
                                         "burst-heavy"))
    p.add_argument("--wait", type=int, default=3600,
                   help="how many seconds I wait for the netem lock")
    a = p.parse_args()

    if a.certify:
        return certify()
    if not a.step:
        p.error("a step is needed, or --certify")

    do_import()
    if a.step in ("restore", "status"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORT))
        _inf("attached to the ports NOT mine: %s"
             % json.dumps(neighbors_not_mine(), ensure_ascii=False))
        return 0 if NETWORK.restore() else 2
    if a.step == "terrain":
        ok = B76.ship_probe()
        _inf("binary md5 %s" % md5_binary())

        return 0 if (B70.terrain_check() and ok) else 2
    if a.step == "detach":
        return detach(a)
    return pair_up(a)


if __name__ == "__main__":
    sys.exit(main())
