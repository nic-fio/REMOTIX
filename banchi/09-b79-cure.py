#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b79-cure — THE TWO CURES OF THE SPIRAL, PAIRED ON A NETWORK THAT LOSES.

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

⭐ It is **the spiral**, and at `perdita-3` it makes 87 keyframes out of 87 frames — the same
   face as the defect of 21 August (144/144).

⭐⭐⭐ AND THE CURE FOR THIS SPIRAL IS ALREADY WRITTEN AND TESTED.  Two
      switches, and they have a MANDATORY ORDER (`src/webtransport.c`):

  · the QUEUE THRESHOLD.  `video_sgombra()` without a threshold abandons the deltas **at
    every frame**; with the threshold it abandons them only when the queue is really
    hopeless (`byte × smoothed_rtt / cwnd` above N ms).  ⛔ It is the
    prerequisite of the other.
  · the RATE REGULATOR: instead of abandoning, it slows down capture.
    ⛔ It comes AFTER the threshold, because as long as `video_sgombra()` empties the queue at
    every frame the quantity it hooks onto (`arretrato`) is **zero by
    construction**, and a mute regulator and a healthy line look the same.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ ON 24 AUGUST 2026 THE DIRECTION OF THE SWITCHES WAS REVERSED, AND THIS
      BENCH WAS **BROKEN** — not «to be updated»: broken, that is unable to give
      red
═══════════════════════════════════════════════════════════════════════════════

`DECISIONI.md` §3.1-septies: the user looked at the cures on the real desktop and
decided they are born **ON** in the product.  ⇒ The new contract:

    video queue threshold     ON at 100 ms      turned off with `--sgombra-soglia-ms 0`
    rate regulator            ON                turned off with `--niente-ritmo-adattivo`

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

    A   --sgombra-soglia-ms 0 --niente-ritmo-adattivo
        ⛔ the TERM OF COMPARISON: the two cures switched off BY HAND.  It is the product
           up to 23 August 2026, byte for byte, obtained from today's binary.
    B   --sgombra-soglia-ms 100 --niente-ritmo-adattivo
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
    most polite way in which a grid lies (`LEZIONI.md` §1.26).

⭐ THE ORDER INSIDE THE PROFILE IS A-B-C, one right after the other, not A-A-A then
   B-B-B: so between the three arms of the same profile three minutes go by, not
   twenty, and the machine is the same machine.  ⚠ It costs 21 server restarts;
   twenty seconds each, and it is the price of pairing.

⛔⭐ AND EVERY ARM IS CHECKED FROM THE SERVER LOG, not from what I
    wrote on the command line (`LEZIONI.md` E1, «written is not in
    force»).  At startup the product ALWAYS writes — on and off — the two
    lines that say the value in force (`sgombra_dichiara()`,
    `wt_ritmo_adattivo()`), and this bench rereads them and stops if they do not
    match.

═══════════════════════════════════════════════════════════════════════════════
⛔ THE SEQUENCE OF AN ARM, and every step has a reason
═══════════════════════════════════════════════════════════════════════════════

 1. **the network is put back smooth**;
 2. **the server is restarted** with the arm's options, and the two startup lines
    are reread;
 3. **a short session is triggered** — the stage and the monitor are born with the first
    client, and the scene would not know where to draw.
    ⛔⭐ And it is triggered **ON A CLEAN NETWORK**, on purpose: `09-b78-apertura.py` has
        measured that a **lost** goodbye and a goodbye **never said** are the same
        fact for the server, and the slot stays taken for `SILENZIO` = 30 s
        (`src/rcp.c:263`) — eleven `CONGEDO 0x0F` in a row, `[M]` 23 August.  If
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
 7. the `qdisc` counters around the run are read, and the `rete-quic` lines
    of the log (`cwnd`, `srtt_us`, `pto_us`, `dgram_persi`, `dgram_falsi`,
    `giudizio=`), which are there in the working tree and not in HEAD.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE REVIEW OF THE EVENING OF 23 AUGUST — «which numbers were dirtied», CHECKED
═══════════════════════════════════════════════════════════════════════════════

Tonight's three-arm grid ran while `_root_che_trascrive`
wrapped `RETE.root` instead of b70's cured `root` (⇒ the box above
that function).  ⇒ It must be said which numbers that line dirtied, and the answer
is READ, not assumed.  There are three checks, and none is a line of reasoning:

 1. ⭐ **THE LINE DIRTIED NOTHING ON THIS GRID — it was a defect still
    to be collected.**  `[R]` at 19:00 on 23 August `09-b70-ritmo.py` at HEAD
    still had `def root(comando, tetto=300): return RETE.root(comando, tetto)`
    (line 1236): b70's cure is from 19:41, **after**.  ⇒ Wrapping `RETE.root`
    was then identical to wrapping `B70.root`, and the defect is PROSPECTIVE —
    it would have bitten the next run, the one with b70 cured.  ⚠ It is exactly the
    reason it must be cured all the same: its face does not change when it starts
    lying.
 2. ⭐ **THE `riga0` WAS THERE, and the server counts are FROM THIS RUN.**  `[R]`
    `09-b76-rete-cattiva.py` at HEAD (line 297) already replaces
    `B70.righe_registro` with its own, which puts the redirect inside a `bash -c`.
    ⇒ b70's defect 2 (the `< file` that steals stdin from `sudo -S`) **did not
    fire**: b79 did not even go through the broken function.
    `[M]` the counter-proof in the numbers, and it is the opposite signature to the cumulative one:
    on all 36 cells `righe_ciclo` sits between **25 and 27** (one 25 s run) and
    `attese_a_vuoto` between **1 973 and 2 156** — constant, not rising.  On
    `ritardo-30` A-B-C gives 2 015 / 2 006 / 2 016.  The cumulative one is visible at a glance
    (`[M]` b70: 4 041 against 1 604, 2.5 times, and rising): here it is not there.
 3. ⭐ **THE COUNT OF ANOTHER RUN IS STRUCTURALLY IMPOSSIBLE HERE**, and not
    by luck: `[R]` `07-b64-terreno.sh:106` does `: > "$LAV/registro.log"` at every
    `accendi`, and this bench restarts the server at **every arm**.
    `[M]` the counter-proof: no pair of cells carries identical numbers from the
    log, and three cells (`perdita-3` A, `raffica-forte` A and B) said
    **«NIENTE DA LEGGERE»** instead of reporting the neighbour's number — which is the
    proof that in the window there was no one else's count to steal.

⭐⭐ AND THE THING THAT COUNTS MOST, and it is a division, not an acquittal:
   **the verdict does not go through the log.**  `[R]` `p_spirale_spenta` (K′),
   `p_ritmo_restituito` (F′) and `p_linea_sana` (S′) read only `n["chiavi"]`,
   `n["fotogrammi"]`, `n["quota_delta"]`, `n["fps"]`, `n["fps_finestra_min"]` and
   `n["deriva_*"]` — all from `misura(giornale, …)`, that is from the client's **§11.1
   trace**.  From the server log come the four numbers that
   CORROBORATE (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`,
   `abbandonati`) and nothing else.
   ⇒ «the spiral switches off, but only with arm C: keyframes from 51.7-88.1 % to
     0.0-5.6 %» and «the healthy line pays nothing» are not log numbers, and
     had nothing to be dirtied by.  ⚠ Redoing the five red profiles
     costs an hour and adds nothing (`LEZIONI.md`, proportionate process).

⭐⭐ AND ONE CELL ONLY WAS REDONE ANYWAY — `ritardo-30` with three arms, which
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
   ⭐ And the new guards spoke: `riga0` = 205 / 219 / 229, `p_registro_letto`
     GREEN on all three, `conti_finali` `[2, 4]` in every arm — that is the two
     counts of the trigger session had already settled and the run wrote two OF ITS OWN.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ THE PREDICATES OF THE PAIR — WRITTEN FIRST, and they return `(passa, perche)`
═══════════════════════════════════════════════════════════════════════════════

Those of the single run are IMPORTED from `09-b70`/`09-b76` and not rewritten
(`p_niente_stacco`, `p_degrada_nel_tempo`, `p_guasto_messo`, `p_coda_mia`).  The
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
  than all the others put together: on `ritardo-30` — which loses zero, reorders
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
⛔⛔ `raffica-forte` — «SESSION DETACHED AT 0.3 s OUT OF 25», and the word is wrong
═══════════════════════════════════════════════════════════════════════════════

`09-b76` gives red on `raffica-forte` with the predicate `p_niente_stacco`, which says
*«delivery lasted 0.3 s out of 25 requested: it detached»*.  ⛔ But that
predicate does not look at the connection: it looks at **how long the delivery of
frames lasted**, and the two things are not the same.  ⇒ The `stacco` step of this
bench asks **who** detached, and asks four independent witnesses:

  1. **the client**, which says it by itself and in full: `01-b3-cliente.py:1979`
     prints *«⭐ still attached after N s: nothing dropped»* and returns 0, or
     *«⛔ I did NOT stay attached: …»* and returns 4;
  2. **the server log**: `congedo motivo=0x..`, `the client takes its farewell`,
     `slot DENIED`, `BANNED`, and the video «final count»;
  3. **the `rete-quic` lines**: `cwnd`, `cwnd_left`, `giudizio=` — if the window
     closed and never reopened, the session is alive and **mute**, which
     is a fact different from detaching and needs a different name;
  4. ⚠ **the third possibility to rule out explicitly**: at 13 % clustered loss
     the HANDSHAKE might not complete, and «it never
     opened» and «it detached» look the same.  ⭐ It is told apart by the
     client itself, which prints `SESSIONE` only when the session is open;
     and `09-b78-apertura.py` has already measured `[M]` that up to **25 %**
     independent loss the session opens 10 times out of 10 in ~1.3 s.

⛔ `IDLE_MS` in `src/trasporto.c` is **30 s**: at 0.3 s it is not that, and indeed the
   `stacco` step rereads it from the source instead of trusting this line.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ WHAT THIS BENCH CANNOT SEE
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **THE IMAGE.**  It counts frames, keyframes, bytes and delay.  «It looks
    better with the cure on» is a verdict of the user on the real desktop.
 2. ⛔ **WHICH ARM IS BETTER.**  See the price, above: it is a choice,
    not a measurement.
 3. ⛔ **THE REAL NETWORK.**  `netem` on `lo`: no radio, no router.
 4. ⛔ **THE BROWSER.**  The client is `01-b3-cliente.py`, which takes the bytes from the
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
    FOUR AND A HALF SECONDS ON `raffica-forte`.**

| profile | arm | fps | worst s | keyframes % | drift end | drift max | Mbit/s wire |
|---|---|---|---|---|---|---|---|
| `ritardo-30` ⭐healthy | A | 39.85 | 36 | 0.0 % | 0.1 | 8.9 | 7.55 |
|                     | B | 40.19 | 37 | 0.0 % | 0.2 | 5.8 | 7.60 |
|                     | C | 39.63 | 36 | 0.0 % | 0.9 | 6.1 | 7.53 |
| `perdita-1`   | A | 11.96 | 5 | **51.7 %** | −2.4 | 76.5 | 3.43 |
|               | B | 32.13 | 17 | 6.4 % | 23.2 | 107.8 | 4.84 |
|               | C | **32.85** | 21 | **0.0 %** | −1.6 | 99.3 | 5.11 |
| `perdita-3`   | A | 7.34 | 5 | **88.1 %** | −40.0 | 53.4 | 2.17 |
|               | B | 20.63 | 11 | ⛔ 23.8 % | 32.9 | 139.3 | 2.90 |
|               | C | 19.63 | 11 | **0.2 %** | −62.2 | 165.7 | 2.79 |
| `jitter-15`   | A | 10.76 | 6 | **59.2 %** | 11.7 | 102.1 | 3.48 |
|               | B | 25.88 | 9 | ⛔ 12.8 % | −65.7 | 64.0 | 8.06 |
|               | C | 21.48 | 15 | **0.0 %** | 53.8 | 168.4 | 6.63 |
| `jitter-30`   | A | 8.56 | 5 | **73.1 %** | 6.7 | 115.6 | 2.55 |
|               | B | 20.25 | 10 | ⛔ 19.9 % | −5.0 | 277.0 | 5.77 |
|               | C | 16.68 | 12 | **0.0 %** | −116.0 | 180.8 | 4.96 |
| `casa-cattiva`| A | 8.28 | 3 | **72.0 %** | −71.5 | 295.3 | 2.21 |
|               | B | 14.37 | 6 | ⛔ 33.6 % | 152.7 | 238.4 | 3.01 |
|               | C | 13.86 | 4 | **5.6 %** | 102.2 | 284.2 | 3.38 |
| ⚠ `raffica-forte` | A | — delivery stops at **4.4 s** out of 25 | | | | | |
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
      at `jitter-15`, 19.9 % at `jitter-30`, 23.8 % at `perdita-3` and 33.6 % at
      `casa-cattiva`, that is above the 10 % of §3.3.  ⇒ K′ is RED on B in
      four profiles out of five and green on C in all five.
   ⭐ The why is read in the server counters: in C `chiave_aspetta` and
      `delta_non_spedito` **collapse** (on `raffica-forte`: 988 → 6 deltas not
      sent, 32 → 0 keyframes waited for).  The threshold alone stops throwing away at
      every frame but the §5.2 debt keeps switching on; the regulator
      prevents it, because the frame does not leave at all.

3. ⭐ **THE RHYTHM COMES BACK, BY 1.7 TO 2.8 TIMES**, and on every red profile: F′ is
   green on B and on C everywhere.  The maximum is `perdita-3`, 7.34 → 20.63/s
   (+181 %); the minimum `casa-cattiva`, 8.28 → 13.86/s (+67 %).
   ⚠ And B almost always gives **more** frames/s than C (25.88 against 21.48 at
     `jitter-15`; 20.25 against 16.68 at `jitter-30`), because C slows
     capture on purpose: ⇒ the two arms are not «less good and better», they are
     **more frames with more keyframes** against **fewer frames all deltas**.

4. ⚠⚠ **THE PRICE, AND IT MUST BE READ NEXT TO THE GAIN.**  On the five ordinary
   profiles the maximum drift grows by **−38 … +161 ms** (worst: `jitter-30`
   B, from 116 to 277 ms; on `casa-cattiva` and `jitter-15` B **drops**).  On
   `raffica-forte` it explodes: **from no measurement to 4.5-7.8 seconds**.
   ⛔ On that line C is not obviously better than A: it is *an image that
      moves with five seconds of delay* against *a still image*.  This
      bench gives the two numbers and **does not choose**: the choice is the user's.

5. ⭐ And the bytes on the wire **go up** with the cure (3.43 → 5.11 Mbit/s at
   `perdita-1`, 3.48 → 8.06 at `jitter-15`): the line was not saturated, it was
   **wasted** — keyframes were being sent instead of deltas.

6. ⭐⭐ **`raffica-forte`: NOBODY DETACHES.**  See the `stacco` step further up and
   the § devoted to it: `[M]` the client stays attached for all 25 s
   («⭐ still attached after 25.0 s: nothing dropped»), the audio arrives for
   the whole run (696 datagrams, purity 1.0000), the server sends no
   `CONGEDO`, no `slot DENIED`, no ban, and the session had opened
   normally (`AMMESSO dopo 1837 ms`).  What stops is **only the delivery of
   frames**.  ⇒ The red of `09-b76` is right as a number and **wrong
   as a word**.  ⭐ And the cures change it: delivery, which in A dies after
   4.4 s, in B and C **lasts all 25 s** (4.2/s with empty seconds inside).

═══════════════════════════════════════════════════════════════════════════════
⭐ THE RUN OF 24 AUGUST 2026 — arms reversed, and the predicate worth most
═══════════════════════════════════════════════════════════════════════════════

`[M]` 24 August 2026, port 7981, user `provanr12`, binary md5
`6ec170c03c6e908eb17d3b056b542813`, `ritardo-30`, 25 s per arm, one run per
cell.  ⛔ It is not a remeasurement of the grid: it is the proof that the REVERSED
bench really runs all the way and that the three arms come into force.

  arm       options                                        fps    keyfr.  drift
  A         --sgombra-soglia-ms 0 --niente-ritmo-adattivo  38.15   0.2 %   1.7 ms
  B         --sgombra-soglia-ms 100 --niente-ritmo-adattivo 39.61  0.0 %  −0.7 ms
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
    python3 banchi/09-b79-cure.py --certifica     ⭐ without a machine
    python3 banchi/09-b79-cure.py terreno
    python3 banchi/09-b79-cure.py stacco          ⛔ the diagnosis of raffica-forte
    python3 banchi/09-b79-cure.py appaia [--secondi 25] [--solo perdita-1]
    python3 banchi/09-b79-cure.py rimetti
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
QUI = os.path.dirname(os.path.abspath(__file__))
MIO = {
    "PORTA": "7940",
    "UTENTE": "provanr4",
    "UID_B": "1040",
    "MACCHINA": "nicfio@192.168.0.2",
    "PAROLA_SUDO": "nicfio",
    "IND": "192.168.0.2",
    "LAV": "/media/REMOTIX/tmp/09nr4",
    "ALBERO": "/media/REMOTIX/src/09nr4-src",
    "DENTRO_ALB": "/srv/src/09nr4-src",
    "DENTRO_LAV": "/srv/remotix/tmp/09nr4",
    "UNITA": "remotix-7940",
    "SHM": "/09nr4",
    # ⛔ The probe port cannot be fixed: `09-b76` lost a whole run
    #    because another agent started a server on it WHILE it
    #    was running.  ⇒ five candidates of mine, and the one free now is chosen.
    "PORTE_SONDA": "7949,7948,7947,7946,7945",
    "FUORI": os.environ.get(
        "FUORI",
        "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
        "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr4"),
}
for _k, _v in MIO.items():
    os.environ[_k] = os.environ.get(_k) or _v

PORTA = int(os.environ["PORTA"])
UTENTE = os.environ["UTENTE"]
LAV = os.environ["LAV"]
ALB = os.environ["ALBERO"]
UNITA = os.environ["UNITA"]
FUORI = os.environ["FUORI"]
PAROLA_SUDO = os.environ["PAROLA_SUDO"]
MACCHINA = os.environ["MACCHINA"]
VIETATA = "enp7s0"
DEV = "lo"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ ALL THE MACHINERY IS IMPORTED — not one line of it is rewritten
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `09-b76-rete-cattiva.py` carries the profiles, the probe, the reduction of the
#    arrivals, the rereading of the rule, the `qdisc` counters and 31 green
#    `--certifica` cases; `09-b70-ritmo.py` carries the reader of the §11.1
#    trace, the reduction to the five numbers and the predicates of the single run.  Two
#    copies of the same reduction in two files are two reductions that diverge
#    (it is the wound of 16 August, `09-b70` line ~430).
B76 = None
B70 = None
RETE = None
LUC = None


def importa(con_rete=True):
    global B76, B70, RETE, LUC
    B76 = _carica("b76rete", os.path.join(QUI, "09-b76-rete-cattiva.py"))
    if not con_rete:
        B76.importa_finto()
        B70 = B76.B70
        return
    B70 = B76.importa()          # ⭐ it is the one that hooks up the network and the lock
    RETE = B76.RETE
    LUC = B76.LUC
    _aggancia_root()                 # ⛔ see `_root_che_trascrive`
    # ⛔⛔ AND THEN WE CHECK THAT THEY TOOK MY ENVIRONMENT, not theirs.
    guai = []
    for nome, mio, suo in (("porta", PORTA, B76.PORTA), ("utente", UTENTE, B76.UTENTE),
                           ("lavoro", LAV, B76.LAV), ("albero", ALB, B76.ALB),
                           ("shm", os.environ["SHM"], B76.SHM),
                           ("dev", DEV, B76.DEV), ("vietata", VIETATA, B76.VIETATA)):
        if str(mio) != str(suo):
            guai.append("%s: the module has «%s», mine is «%s»" % (nome, suo, mio))
    if RETE.PORTA != PORTA or RETE.DEV != DEV or RETE.VIETATA != VIETATA:
        guai.append("the network module has port %d, dev «%s», forbidden «%s»"
                    % (RETE.PORTA, RETE.DEV, RETE.VIETATA))
    if guai:
        raise SystemExit("⛔ I DO NOT MEASURE: the import did not take my environment — "
                         + " · ".join(guai))


def root(comando, tetto=300):
    """⛔ This file's `root` too goes through the CURED chain when there is one.

    ⚠ The commands of this file are all already written inside a `bash -c "…"`
      of their own — it is the discipline of `09-b76` — so here not a number changes.
      But the discipline is a convention, and a convention is forgotten by the
      next one who adds a line: `RETE.root` alone would give them a plausible
      `0` instead of an error (⇒ the box above `_aggancia_root`).
    """
    if _ROOT_CURATA is not None:
        return _ROOT_CURATA(comando, tetto)
    return RETE.root(comando, tetto)


# ⛔⛔ THE CLIENT MUST BE LISTENED TO IN FULL, and it is not.
#
#    `09-b70.giro()` keeps `coda_cliente = testo[-400:]`, which is enough for the
#    five numbers and **not** for the question «who detached»: `[M]` 23 August
#    2026, those 400 bytes hold the three final audio lines and do not hold
#    the line that answers — *«⭐ still attached after 25.0 s»*
#    (`01-b3-cliente.py:1979`).  ⇒ The first `stacco` run refused to
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
# Until 23 August 2026 this function called **`RETE.root`**, that is it skipped
# `09-b70-ritmo.py:root()` and went straight to the step below.  ⛔ It is a defect
# that **cannot be seen by reading either of the two files**: here the line is correct (a
# `root` calling a `root`), and there the cure is written and tested — only
# nobody runs it any more.  It is the second one this project pays for in one evening.
#
# ⛔ `RETE.root` (`07-b64-rete.py:238`) is a single `sudo` **in front of the bare
#    command**:  `printf parola | sudo -S -p '' <comando>`.  From there come two
#    defects, and they are those `09-b70` cured on 23 August:
#      1. `sudo` covers **only the first link** of the chain: in `a && b > c` the
#         `b` and the `>` run as the USER, not as root.  `[M]` the reader of the
#         §11.1 trace was not written, and §11.1 stayed without a referee;
#      2. a trailing `< file` **steals stdin from `sudo -S`** (the redirect belongs to the
#         shell and goes to the LAST command of the pipeline, which is `sudo`): the password
#         does not arrive, `sudo` exits 1, and the number comes back **0 in silence**.  `[M]`
#         `righe_registro()` returned 0, `conti_del_server()` read the log
#         **from server startup** instead of from the run, and `attese_a_vuoto`
#         became cumulative: 4 041 against 1 604 on a still run, 2.5 times.
#
# ⭐ `09-b70.root()` cures both with a single line — `catena_root()`, that is
#    **one** `sudo` and the whole chain inside ITS `bash -c`.  ⇒ Whoever wraps to
#    transcribe must wrap **that one**, or brings the two defects back in
#    by going through a function named like the cured one.
#
# ⛔⛔ AND WRITING `B70.root` IS NOT ENOUGH: when this file arrives, `B70.root` **has
#     already been replaced** by `09-b76-rete-cattiva.py:416`, with a wrapper
#     that in turn calls `RETE.root`.  Wrapping `B70.root` then would
#     mean wrapping someone else's defect and calling it a cure.  ⇒ The cured
#     chain is rebuilt **from its pieces** — `B70.catena_root` + `RETE.rem` — which
#     are what `09-b70.root()` does, and do not go through any substitute.
#
# ⚠ And it is hooked ONCE ONLY: `appaia()` does 21 cells in the same process
#   and `importa()` can be called more than once.  A repeated wrapper
#   does not get the numbers wrong, but it nests 21 calls and the first diagnosis
#   becomes unreadable.
ULTIMO_CLIENTE = {"testo": ""}
_ROOT_CURATA = None


def _aggancia_root():
    """Installs the transcriber ON TOP OF b70's cured `root` — once only."""
    global _ROOT_CURATA
    if _ROOT_CURATA is not None:
        return
    if not hasattr(B70, "catena_root"):
        raise SystemExit(
            "⛔ I DO NOT MEASURE: «09-b70-ritmo.py» has no `catena_root()`, that is it is the "
            "version with `sudo -S` in front of the bare command.  On that one a "
            "trailing `< file` steals the password from sudo and the server counts "
            "become cumulative from startup (2.5 times, `[M]` 23 Aug 2026). "
            "Align the tree before measuring.")
    _ROOT_CURATA = lambda c, tetto=300: RETE.rem(B70.catena_root(c), tetto)
    B70.root = _root_che_trascrive


def _root_che_trascrive(comando, tetto=300):
    rc, out, err = _ROOT_CURATA(comando, tetto)
    if "01-b3-cliente.py" in comando:
        ULTIMO_CLIENTE["testo"] = out + err
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
BRACCI = [
    ("A", "--sgombra-soglia-ms 0 --niente-ritmo-adattivo", 0, False,
     "⛔ the two cures switched OFF BY HAND: it is the term of comparison, that is the product "
     "up to 23 August 2026 — and it is remeasured TODAY, on today's binary"),
    ("B", "--sgombra-soglia-ms 100 --niente-ritmo-adattivo", 100, False,
     "⭐ the QUEUE THRESHOLD ALONE: a stuck delta is abandoned only when the "
     "queue is hopeless for more than 100 ms, not at every frame"),
    ("C", "", 100, True,
     "⭐⭐ THE DEFAULTS since 24 August 2026 (DECISIONI.md §3.1-septies): the "
     "threshold PLUS the rate regulator, and NO option on the command "
     "line — it is the product that ships"),
]

# ⛔ The two lines the product writes at startup, ALWAYS, on and off.
#    They are the contract on which the arm is checked (`LEZIONI.md` E1).
RE_SOGLIA = re.compile(r"video queue threshold \(§5\.1\): (\d+) ms")
RE_RITMO_ACCESO = re.compile(r"the rate regulator is ON")
RE_RITMO_SPENTO = re.compile(r"the rate regulator is OFF")


def riavvia(opzioni, soglia_attesa, ritmo_atteso):
    """⛔⭐ The server restarts with the arm's options, and THEN the log is
       reread to know what is REALLY in force.

    `LEZIONI.md` E1 — «written is not in force».  An old binary
    would refuse `--sgombra-soglia-ms` and would not start; a right binary with
    a typo in the option would start with the cure OFF and give three identical
    arms, that is «the cure is not needed» on a cure never switched on.
    ⇒ Returns `(ok, righe)`, and `ok` is false if the two lines do not match.
    """
    amb = " ".join("%s=%s" % (k, os.environ[k]) for k in
                   ("PORTA", "IND", "UTENTE", "UID_B", "ALBERO", "LAV",
                    "DENTRO_ALB", "DENTRO_LAV", "UNITA", "MACCHINA",
                    "PAROLA_SUDO"))
    import subprocess
    p = subprocess.run(
        "%s OPZIONI_SERVER=%s bash %s/09-b79-terreno.sh accendi"
        % (amb, json.dumps(opzioni), os.path.join(QUI)),
        shell=True, capture_output=True, timeout=300)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    if "server " not in testo:
        return False, ["⛔ the server did not start: %s" % testo[-300:]]
    # ⛔ The log was emptied by the startup: the startup lines are
    #    the first ones, and we wait for them to be there instead of reading whatever is there.
    righe = []
    for _ in range(30):
        rc, out, _e = root("bash -c \"grep -a 'video queue threshold\\|"
                           "rate regulator' %s/registro.log | head -4\"" % LAV)
        righe = [x for x in out.splitlines() if x.strip()]
        if len(righe) >= 2:
            break
        time.sleep(0.3)
    testo_righe = "\n".join(righe)
    m = RE_SOGLIA.search(testo_righe)
    letta = int(m.group(1)) if m else None
    acceso = bool(RE_RITMO_ACCESO.search(testo_righe))
    spento = bool(RE_RITMO_SPENTO.search(testo_righe))
    guai = []
    if letta is None:
        guai.append("the threshold line is not in the log")
    elif letta != soglia_attesa:
        guai.append("the threshold in force is %d ms, requested %d" % (letta, soglia_attesa))
    if ritmo_atteso and not acceso:
        guai.append("the rate regulator does NOT appear to be on")
    if (not ritmo_atteso) and not spento:
        guai.append("the rate regulator does NOT appear to be off")
    return (not guai), (righe + (["⛔ " + g for g in guai] if guai else []))


def md5_binario():
    """⚠ The binary I measure must be the one I think, and it is declared."""
    rc, out, _ = root("md5sum %s/src/remotix" % ALB)
    return out.strip().split()[0] if out.strip() else "?"


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREVIOUS SESSION MUST HAVE FINISHED CLOSING — and it is not obvious
# ═══════════════════════════════════════════════════════════════════════════
#
# `[M]` 23 August 2026, found on `07-b64-rete.py` (`registro_posato()`, line
# 497) and brought here **without touching that file**: closing a session is
# SLOW when the pacer has a queue — the profile at 10 % loss took
# **29 s more** than the others to write its «final count».  ⇒ Two faults,
# and they have the same root:
#
#  1. **the count read belongs to another run.**  `riga0` of the new run is taken
#     BEFORE the line of the old run is written; that line falls inside the
#     window, and `conti_del_server()` — which takes the LAST one after `riga0` — reads
#     it as its own.  `[M]` three profiles in a row reported «sent 4999 ·
#     refused 3 · deferred 7410», which was the count of the FIRST of the three;
#  2. **the slot is still taken.**  Until the old session has
#     closed, §4.4-bis refuses the new one with `CONGEDO 0x0F GIA_ATTIVA_REMOTA`, and
#     the lock lasts until `SILENZIO` = 30 s (`09-b78-apertura.py` §4).
#     ⇒ A run can fail because of the run BEFORE, and three arms measured in
#       a row stop being comparable.
#
# ⭐⭐ AND IN HERE THE FIRST IS STRUCTURALLY IMPOSSIBLE — it is written because
#     it is a verified fact, not a hope: `07-b64-terreno.sh:106` does
#     `: > "$LAV/registro.log"` at EVERY `accendi`, and this bench restarts the
#     server at **every arm** (`riavvia()`).  ⇒ In the window of an arm there
#     is no count of the previous arm to steal, and the slot is free because
#     the process holding it is dead.  `[M]` the counter-proof on the 36 runs of
#     23 August: no pair of cells carries identical numbers from the log, and
#     three cells (`perdita-3` A, `raffica-forte` A and B) said «NIENTE DA
#     LEGGERE» instead of reporting the neighbour's number.
#
# ⛔ What STAYS uncovered, and that is why the two functions are there: inside
#    ONE arm before the run there is the **trigger session**, and its «final
#    count» sits in the same log.  If it arrived late it would fall into the
#    window of the run.  ⇒ We wait for the count to be STILL, and then the run
#    DEMANDS a line of its own.
def conta_conti_finali():
    rc, out, _ = root("bash -c \"grep -ac 'final count' %s/registro.log "
                      "2>/dev/null || true\"" % LAV)
    t = out.strip()
    return int(t) if t.isdigit() else None


def registro_posato(tetto=60.0, quiete=3.0):
    """Waits until the count of «final count» lines stays still for `quiete` s.

    Returns that count — it is the `n0` from which the new run demands a line OF ITS OWN — or
    `None` if the log was not read (⛔ and `None` is not zero).
    """
    n = conta_conti_finali()
    if n is None:
        return None
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        if m is None:
            return None
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    if fermo < quiete:
        _dub("⚠ in %.0f s the log did not settle: someone is still "
             "closing a session" % tetto)
    return n


def conto_e_mio(n0, n):
    """⛔ Is the «final count» inside `n["server"]` from THIS run, or not?

    ⇒ If the count of lines has not grown, the line read is from before (at
      worst from the trigger session) and the four server-side numbers **must not be
      judged**.  They are not deleted: they are marked, which is the difference between
      «I did not read» and «nothing happened» (`LEZIONI.md` §1.9).
    """
    s = (n or {}).get("server") or {}
    if n0 is None:
        s["conto_dubbio"] = ("⛔ I do not know how many «final count» there were before the "
                             "run: I do not judge the server-side numbers")
        return False
    n1 = conta_conti_finali()
    if n1 is None or n1 <= n0:
        s["conto_dubbio"] = ("⛔ this run did not write a «final count» OF ITS OWN "
                             "(they were %s, they are %s): the line read is from before — "
                             "I do NOT judge the server-side numbers" % (n0, n1))
        return False
    s["conti_finali"] = [n0, n1]
    return True


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE `rete-quic` LINES — which are there in the working tree and not in HEAD
# ═══════════════════════════════════════════════════════════════════════════
def leggi_rete_quic(riga0):
    """⭐ `src/webtransport.c:3772` fixes the format as a TEXT CONTRACT:
       prefix `rete-quic`, fields `nome=valore` without spaces, and `giudizio=`
       last, with the value running to the end of the line.  ⇒ `split()` and `split('=',1)`.

    ⛔ It judges nothing: it reduces and prints.  ⚠ `dgram_falsi` = datagrams
       declared lost and then acknowledged = **reordering measured on the
       server side**, and it holds for audio only (streams have no
       per-piece identifier: the price is declared).
    """
    rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                      "'rete-quic ' | tail -400\"" % (riga0 + 1, LAV))
    righe = [r for r in out.splitlines() if "rete-quic " in r]
    if not righe:
        return {"esito": "NIENTE DA LEGGERE — no «rete-quic» line in this run"}
    campi = []
    for r in righe:
        d = {}
        corpo = r.split("rete-quic ", 1)[1]
        giud = None
        if "giudizio=" in corpo:
            corpo, giud = corpo.split("giudizio=", 1)
        for pezzo in corpo.split():
            if "=" in pezzo:
                k, v = pezzo.split("=", 1)
                d[k] = v
        d["giudizio"] = (giud or "").strip()
        campi.append(d)

    def num(d, k):
        v = d.get(k)
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def elenco(k):
        return [x for x in (num(d, k) for d in campi) if x is not None]

    ultima = campi[-1]
    giudizi = {}
    for d in campi:
        giudizi[d["giudizio"]] = giudizi.get(d["giudizio"], 0) + 1
    cwnd = elenco("cwnd")
    srtt = elenco("srtt_us")
    rttv = elenco("rttvar_us")
    n = {"esito": "letto", "righe": len(campi),
         "persi_tot": num(ultima, "persi"),
         "spediti_tot": num(ultima, "spediti"),
         "cwnd_min": min(cwnd) if cwnd else None,
         "cwnd_mediana": sorted(cwnd)[len(cwnd) // 2] if cwnd else None,
         "cwnd_fine": num(ultima, "cwnd"),
         "srtt_us_mediana": sorted(srtt)[len(srtt) // 2] if srtt else None,
         "srtt_us_max": max(srtt) if srtt else None,
         "rttvar_us_mediana": sorted(rttv)[len(rttv) // 2] if rttv else None,
         "pto_us_fine": num(ultima, "pto_us"),
         "dgram_persi": num(ultima, "dgram_persi"),
         "dgram_falsi": num(ultima, "dgram_falsi"),
         "dgram_ok": num(ultima, "dgram_ok"),
         "giudizi": giudizi}
    return n


def stampa_rete_quic(n):
    if n.get("esito") != "letto":
        _dub("QUIC    %s" % n.get("esito"))
        return
    _inf("QUIC    %d lines · lost %s packets out of %s sent · cwnd min %s / "
         "median %s / end %s"
         % (n["righe"], n["persi_tot"], n["spediti_tot"], n["cwnd_min"],
            n["cwnd_mediana"], n["cwnd_fine"]))
    _inf("        srtt median %s us (max %s) · rttvar median %s us · final "
         "pto %s us"
         % (n["srtt_us_mediana"], n["srtt_us_max"], n["rttvar_us_mediana"],
            n["pto_us_fine"]))
    _inf("        datagrams (audio): lost %s · acknowledged %s · ⭐ FALSE "
         "%s (= reordering measured by the server)"
         % (n["dgram_persi"], n["dgram_ok"], n["dgram_falsi"]))
    _inf("        server judgements: %s"
         % json.dumps(n["giudizi"], ensure_ascii=False))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE PREDICATES OF THE PAIR — written FIRST
# ═══════════════════════════════════════════════════════════════════════════
#
# ── the thresholds, in one place only, and each with its reason ────────────
QUOTA_CHIAVI_MAX = 0.10   # ⛔ the complement of `QUOTA_DELTA = 0.90` of 09-b70,
                          #    that is §3.3 read backwards.  It is not a new
                          #    threshold: it is the same, and two thresholds for the same
                          #    fact are two thresholds that diverge.
RUMORE = 0.05             # ⚠ 09-b70 estimates at 5 % the difference between two runs
                          #    of the same machine
DIFFERENZA_MINIMA = 0.10  # ⛔ TWICE the noise: below it, this bench does not
                          #    judge instead of calling the noise an «effect»
DERIVA_TOLLERATA_MS = 100.0  # ⭐ = the threshold itself: the cure keeps a delta
                             #   until the queue is hopeless for more
                             #   than N ms, so the delay it can add
                             #   is N by construction


def _quota_chiavi(n):
    if not B70._ha_misurato(n):
        return None
    return round(1.0 - n["quota_delta"], 4)


def p_spirale_spenta(a, x, etichetta):
    """**K′ — THE CURE SWITCHES OFF THE SPIRAL.**

    ⛔ And it is SILENT where the spiral was not there in A: putting out a fire that is not there
       is not a merit, and it is a green that would award itself.
    """
    if not B70._ha_misurato(a):
        return _muto("arm A did not measure: without it there is no "
                     "pair, and a number without a denominator does not judge")
    if not B70._ha_misurato(x):
        return _muto("arm %s did not measure: %s"
                     % (etichetta, x.get("esito", "?")))
    qa, qx = _quota_chiavi(a), _quota_chiavi(x)
    coda = ("keyframes %d out of %d = %.1f %% in arm %s, against %d out of %d = "
            "%.1f %% in A" % (x["chiavi"], x["fotogrammi"], qx * 100, etichetta,
                              a["chiavi"], a["fotogrammi"], qa * 100))
    if qa <= QUOTA_CHIAVI_MAX:
        return _muto("in A the spiral was NOT there (%.1f %% keyframes, below "
                     "%.0f %%): there is nothing to switch off, and a green here I "
                     "would award myself — %s"
                     % (qa * 100, QUOTA_CHIAVI_MAX * 100, coda))
    if qx <= QUOTA_CHIAVI_MAX:
        return _si("⭐ THE SPIRAL HAS SWITCHED OFF: %s" % coda)
    return _no("⛔ the spiral did NOT switch off: %s" % coda)


def p_ritmo_restituito(a, x, etichetta):
    """**F′ — THE CURE GIVES BACK RHYTHM**, and the threshold is twice the noise.

    ⚠ Three outcomes, not two: below a 10 % difference this bench says
      «indistinguishable» instead of calling the noise an effect.
    """
    if not B70._ha_misurato(a) or not B70._ha_misurato(x):
        return _muto("one of the two arms did not measure: A «%s», %s «%s»"
                     % (a.get("esito", "?"), etichetta, x.get("esito", "?")))
    if not a["fps"]:
        return _muto("arm A has zero frames/s: there is no ratio")
    r = x["fps"] / a["fps"]
    coda = ("%.2f/s in arm %s against %.2f/s in A (%.0f %%) · worst "
            "second %s against %s · ⚠ AND THE PRICE: final drift %s ms against "
            "%s ms (maximum %s against %s)"
            % (x["fps"], etichetta, a["fps"], r * 100, x["fps_finestra_min"],
               a["fps_finestra_min"], x["deriva_fine_ms"], a["deriva_fine_ms"],
               x["deriva_max_ms"], a["deriva_max_ms"]))
    if r >= 1.0 + DIFFERENZA_MINIMA:
        return _si("⭐ the rhythm has come back: %s" % coda)
    if r <= 1.0 - DIFFERENZA_MINIMA:
        return _no("⛔ THE CURE TAKES RHYTHM AWAY instead of giving it: %s" % coda)
    return _muto("indistinguishable from noise (less than %.0f %%, which is "
                 "twice the %.0f %% between two runs of the same machine): %s"
                 % (DIFFERENZA_MINIMA * 100, RUMORE * 100, coda))


def p_linea_sana(bracci):
    """**S′ — THE CURE DOES NOT COST ON THE HEALTHY LINE**, and it is worth more than all the
       others put together.

    ⛔ On `ritardo-30` there is nothing to cure: zero loss, zero reordering,
       only thirty milliseconds of delay.  ⇒ The three arms must be
       indistinguishable, and if they are not it is the most important discovery of the
       run — because it would mean the cure is paid for even where it is not needed.

    `bracci` = {"A": n, "B": n, "C": n}
    """
    a = bracci.get("A") or {}
    if not B70._ha_misurato(a):
        return _muto("arm A of the healthy line did not measure: %s"
                     % a.get("esito", "?"))
    guai, detto = [], []
    for et in ("B", "C"):
        x = bracci.get(et) or {}
        if not B70._ha_misurato(x):
            return _muto("arm %s of the healthy line did not measure: %s"
                         % (et, x.get("esito", "?")))
        r = x["fps"] / a["fps"] if a["fps"] else 0.0
        dq = _quota_chiavi(x)
        dd = x["deriva_fine_ms"] - a["deriva_fine_ms"]
        detto.append("%s %.2f/s (%.0f %%), keyframes %.1f %%, drift %s ms "
                     "(%+.0f against A)"
                     % (et, x["fps"], r * 100, dq * 100, x["deriva_fine_ms"], dd))
        if abs(r - 1.0) > RUMORE:
            guai.append("%s: %.2f/s against %.2f/s = %.0f %%, beyond the %.0f %% "
                        "of noise" % (et, x["fps"], a["fps"], r * 100,
                                       RUMORE * 100))
        if dq > QUOTA_CHIAVI_MAX:
            guai.append("%s: %.1f %% keyframes on a line that loses "
                        "nothing" % (et, dq * 100))
        if dd > DERIVA_TOLLERATA_MS:
            guai.append("%s: the final drift grows by %.0f ms, more than the "
                        "threshold itself (%.0f ms) — it is not the threshold "
                        "at work" % (et, dd, DERIVA_TOLLERATA_MS))
    coda = "A %.2f/s, keyframes %.1f %%, drift %s ms · %s" % (
        a["fps"], _quota_chiavi(a) * 100, a["deriva_fine_ms"], " · ".join(detto))
    if guai:
        return _no("⛔⛔ THE CURE COSTS ON THE HEALTHY LINE — %s · %s"
                   % (" · ".join(guai), coda))
    return _si("the three arms are indistinguishable on the healthy line: %s" % coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE POSITIVE CONTROL — «how does this bench know it can see?»
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `PIANO.md` §0.3.4: *«a bench that cannot see the defect it looks for has no
#    right to green»*.  Here pairs are built and we check that the three
#    predicates give what is written FIRST — green, red **and mute**.
def _g(fps, chiave_ogni=0, deriva=0.0, secondi=25):
    """A fake run, reduced by the SAME `misura()` that runs on the real runs."""
    return B76._fab_giro(fps, secondi=secondi, chiave_ogni=chiave_ogni,
                         deriva=deriva)


def certifica():
    print("⭐ CERTIFICATION OF THE TWO-CURES BENCH — the expected outcome is written "
          "FIRST\n")
    print("   ⛔ No contact with the test machine: here the TOOL is tested,"
          "\n      not the product.\n")
    importa(con_rete=False)
    verde = True

    def esito(nome, visto, atteso, perche):
        nonlocal verde
        bene = (visto is atteso)
        verde = verde and bene
        print("  %s%-64s atteso %-5s visto %-5s\n        %s"
              % ("OK  " if bene else "⛔  ", nome, atteso, visto, perche[:170]))

    # ── 1 · K′ · does the spiral switch off? ───────────────────────────────
    print("  ── K′ · the cure switches off the spiral ──\n")
    # ⭐ `chiave_ogni=1` = all frames are keyframes: it is the face of the
    #    defect of 21 August (144 keyframes out of 144).
    spirale = _g(10, chiave_ogni=1)
    sana = _g(40)
    p, q = p_spirale_spenta(spirale, sana, "B")
    esito("1-⭐ A is all keyframes, B has none: the spiral has switched off",
          p, True, q)

    p, q = p_spirale_spenta(spirale, _g(12, chiave_ogni=1), "B")
    esito("2-⛔⛔ A is all keyframes and so is B: the cure switched off nothing",
          p, False, q)

    p, q = p_spirale_spenta(sana, _g(41), "B")
    esito("3-⭐⭐ in A the spiral was NOT there: the bench is SILENT instead of taking "
          "a green it would award itself", p, None, q)

    p, q = p_spirale_spenta(B70.misura([], 25, None, None), sana, "B")
    esito("4-⛔ arm A did not measure: without a denominator, it is SILENT",
          p, None, q)

    # ── 2 · F′ · does the rhythm come back? and below the noise it is SILENT ─
    print("\n  ── F′ · the cure gives back rhythm (and noise is not an "
          "effect) ──\n")
    p, q = p_ritmo_restituito(_g(10), _g(40), "B")
    esito("5-⭐ from 10/s to 40/s: the rhythm has come back", p, True, q)

    p, q = p_ritmo_restituito(_g(40), _g(41), "B")
    esito("6-⭐⭐ 40 against 41: it is 2.5 %, less than twice the noise — the "
          "bench does NOT call the noise an effect and is SILENT", p, None, q)

    p, q = p_ritmo_restituito(_g(40), _g(20), "C")
    esito("7-⛔⛔ THE CURE TAKES RHYTHM AWAY: 40/s in A and 20/s in C — and it is the "
          "most important discovery that could come out of here", p, False, q)

    # ⚠⚠ THE BOUNDARY, and it must be tested from BOTH sides — a three-outcome
    #    predicate goes wrong right there in the middle.  ⛔ And the first expectation I had
    #    written was WRONG: I had taken as «above the boundary» a 44 against
    #    40, which the builder renders as 44.04 against 40.04 = **109.99 %**, that is
    #    a hair BELOW.  ⇒ The case was not fixed by moving the threshold:
    #    the EXPECTATION was fixed, which was mine and not the predicate's.
    p, q = p_ritmo_restituito(_g(40), _g(44), "B")
    esito("8-⚠ a hair BELOW the boundary (109.99 %): the bench is silent",
          p, None, q)

    p, q = p_ritmo_restituito(_g(40), _g(45), "B")
    esito("9-⚠ one step ABOVE the boundary (112.5 %): the bench judges",
          p, True, q)

    # ── 3 · S′ · ⛔ the healthy line, worth more than all the others ───────
    print("\n  ── ⛔⛔ S′ · the cure must not cost on the healthy line ──\n")
    p, q = p_linea_sana({"A": _g(40), "B": _g(40.5), "C": _g(39.6)})
    esito("10-⭐ the three arms within 5 %: indistinguishable", p, True, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40.2), "C": _g(34)})
    esito("11-⛔⛔ THE DEFECT THIS PREDICATE EXISTS TO FIND: C loses "
          "15 % on the HEALTHY line", p, False, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40, chiave_ogni=1), "C": _g(40)})
    esito("12-⛔⛔ B is all keyframes on a line that loses nothing: the cure "
          "SWITCHED ON a spiral where there was none", p, False, q)

    # ⭐ The price, and it is the case the mandate asks not to confuse with an
    #   improvement: same rhythm, but the delay grows more than the threshold.
    p, q = p_linea_sana({"A": _g(40), "B": _g(40, deriva=0.0),
                         "C": _g(40, deriva=0.5)})
    esito("13-⛔⭐ THE PRICE: C keeps the rhythm but the drift grows more than the "
          "threshold itself (100 ms) — it is not the threshold at work", p, False, q)

    p, q = p_linea_sana({"A": _g(40), "B": _g(40),
                         "C": B70.misura([], 25, None, None)})
    esito("14-⛔ one arm of the healthy line did not measure: SILENT", p, None, q)

    # ── 4 · ⛔ the arm is checked from the LOG, not from the command line ───
    print("\n  ── ⛔ «written is not in force»: the two startup lines ──\n")
    # ⚠ Here the machine is not touched: the RECOGNISER is exercised on the real
    #   lines the product writes (`sgombra_dichiara`, `wt_ritmo_adattivo`).
    # ⛔ Updated on 10 Oct 2026 to the lines the product writes NOW, in English
    #    (`sgombra_dichiara()` and `wt_ritmo_adattivo()` in `src/webtransport.c`).
    #    ⚠ They are not made up: they are the product's text, shortened at the tail.
    vere_A = ("⛔ PHASE 9, video queue threshold (§5.1): 0 ms — OFF: "
              "it abandons at every more recent frame, that is the "
              "product up to 23 Aug 2026 byte for byte.  ⚠ And it is NOT "
              "the default: since 24 August it is born ON at 100 ms, so "
              "someone typed `--sgombra-soglia-ms 0` on purpose.\n"
              "⛔ the rate regulator is OFF by whoever launched the "
              "server (`--niente-ritmo-adattivo`): no frame "
              "will ever be skipped because of the line")
    vere_C = ("⭐ PHASE 9, video queue threshold (§5.1): 100 ms — "
              "ON: above the threshold a stuck delta is abandoned, below "
              "it is KEPT.  ⭐ It is the DEFAULT since 24 Aug 2026\n"
              "⭐ PHASE 9: the rate regulator is ON — a frame "
              "does NOT leave when 2 deltas in flight still have bytes in my "
              "output queue.  ⭐ It is the DEFAULT since 24 Aug 2026")

    def riconosci(testo, soglia, ritmo):
        m = RE_SOGLIA.search(testo)
        letta = int(m.group(1)) if m else None
        acceso = bool(RE_RITMO_ACCESO.search(testo))
        spento = bool(RE_RITMO_SPENTO.search(testo))
        if letta != soglia:
            return False, "the threshold in force is %s, requested %s" % (letta, soglia)
        if ritmo and not acceso:
            return False, "the regulator does not appear to be on"
        if (not ritmo) and not spento:
            return False, "the regulator does not appear to be off"
        return True, "threshold %s ms, regulator %s" % (letta,
                                                       "on" if ritmo else "off")

    p, q = riconosci(vere_A, 0, False)
    esito("15-⭐ arm A recognised from the product's real lines", p, True, q)
    p, q = riconosci(vere_C, 100, True)
    esito("16-⭐ arm C recognised from the product's real lines", p, True, q)
    p, q = riconosci(vere_A, 100, False)
    esito("17-⛔⛔ threshold 100 REQUESTED and 0 in force: the bench STOPS "
          "instead of measuring three identical arms and concluding «the cure is not "
          "needed»", p, False, q)
    p, q = riconosci(vere_C, 100, False)
    esito("18-⛔ the regulator requested OFF and it appears on", p, False, q)

    # ── 5 · the reduction of the `rete-quic` lines, which is a text contract ─
    print("\n  ── ⭐ the `rete-quic` lines: the text contract ──\n")
    finte = [
        "12:00:01.000 wt      rete-quic 192.168.0.2:52344 da_ms=0 persi=0 "
        "persi_d=0 cwnd=14000 cwnd_left=14000 srtt_us=30100 rttvar_us=900 "
        "pto_us=132000 spediti=100 dgram_persi=0 dgram_ok=10 dgram_falsi=0 "
        "giudizio=-- nothing to report",
        "12:00:02.000 wt      rete-quic 192.168.0.2:52344 da_ms=1000 persi=7 "
        "persi_d=7 cwnd=6000 cwnd_left=0 srtt_us=41230 rttvar_us=11400 "
        "pto_us=132000 spediti=210 dgram_persi=5 dgram_ok=40 dgram_falsi=3 "
        "giudizio=⛔ the line is losing",
    ]
    salvato = globals().get("root")
    globals()["root"] = lambda c, tetto=300: (0, "\n".join(finte), "")
    n = leggi_rete_quic(0)
    globals()["root"] = salvato
    esito("19-⭐ two lines reduced: lost 7, cwnd min 6000, ⭐ dgram_falsi 3 "
          "(= reordering seen by the server)",
          (n["righe"] == 2 and n["persi_tot"] == 7 and n["cwnd_min"] == 6000
           and n["dgram_falsi"] == 3 and n["srtt_us_max"] == 41230),
          True, json.dumps({k: n[k] for k in ("righe", "persi_tot", "cwnd_min",
                                              "dgram_falsi", "srtt_us_max")}))
    esito("20-⭐ and `giudizio=` runs to the end of the line, spaces included",
          (n["giudizi"].get("⛔ the line is losing") == 1
           and n["giudizi"].get("-- nothing to report") == 1),
          True, json.dumps(n["giudizi"], ensure_ascii=False))

    salvato = globals().get("root")
    globals()["root"] = lambda c, tetto=300: (0, "", "")
    n = leggi_rete_quic(0)
    globals()["root"] = salvato
    esito("21-⛔ no `rete-quic` line: «I did not read» is not «zero» "
          "(`CODER.md` §3.10)", n.get("esito") != "letto", True, n.get("esito"))

    print("\n== %s" % ("⭐ THE BENCH CAN SEE THE DEFECTS IT LOOKS FOR — and can stay SILENT "
                       "where it cannot judge"
                       if verde else
                       "⛔⛔ THE BENCH CANNOT SEE WHAT IT LOOKS FOR: none of its greens "
                       "is to be believed"))
    return 0 if verde else 1


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def vicini_non_miei():
    """⚠ `LEZIONI.md` §1.26: two benches on the same machine do not give a
       red, they give **a plausible number**.  ⛔ The 7930 of `09-b76` was left
       on: it is not mine and it is not switched off, but if someone attached to it my
       numbers would be dirty.  ⇒ We count who is ATTACHED, not who
       listens: a server on and idle is not a running bench."""
    fuori = {}
    for p in ("7900", "7910", "7920", "7930", "7932", "7730"):
        rc, out, _ = root("bash -c \"ss -uan 2>/dev/null | grep ':%s ' | "
                          "grep -vc UNCONN || true\"" % p)
        fuori[p] = out.strip()
    rc, out, _ = root("uptime")
    fuori["carico"] = out.strip()[-32:]
    return fuori


def profilo(nome):
    for p in B76.PROFILI:
        if p[0] == nome:
            return p
    return None


def installa_profilo(regole):
    """⛔ `del root` + `add`, never `change`: `[M]` 23 Aug 2026, `tc qdisc change`
       is STICKY and dragged a `reorder` along for four profiles
       — which would have measured a network nobody had asked for."""
    ok, q = RETE.stringi(B76._regole(regole))
    if not ok:
        return False, q, ""
    B76.filtri_sonda()
    riletta = B76.regola_riletta()
    passa, perche = B76.controlla_regola(regole, riletta)
    return passa, perche, riletta


def una_casella(nome_profilo, regole, verifica, etichetta, opzioni, soglia,
                ritmo, secondi):
    """One arm of a profile: the sequence of the seven steps of the header."""
    voce = {"profilo": nome_profilo, "braccio": etichetta, "opzioni": opzioni}

    # 1 · the network is put back smooth, so the trigger session is born clean
    RETE.rimetti(dillo=False)
    # 2 · the server restarts with the arm, and the arm is CHECKED
    ok, righe = riavvia(opzioni, soglia, ritmo)
    voce["avvio"] = righe
    for r in righe:
        _inf("AVVIO   %s" % r.split("avvio   ")[-1][:150])
    if not ok:
        _ko("⛔ arm %s is NOT in force: I do not measure this cell"
            % etichetta)
        voce["esito"] = "IL BRACCIO NON E' IN VIGORE"
        return voce
    # 3 · the trigger session, ON A CLEAN NETWORK (see the header, point 3)
    if not B70.innesca_sessione():
        _ko("the trigger session does not open: I do not measure this cell")
        voce["esito"] = "LA SESSIONE D'INNESCO NON SI APRE"
        return voce
    # 4 · the profile, and it is reread
    passa_r, perche_r, riletta = installa_profilo(regole)
    voce["regola_riletta"] = riletta
    (_ok if passa_r else _ko)("the rule: %s" % perche_r)
    if not passa_r:
        voce["esito"] = "LA REGOLA INSTALLATA NON E' QUELLA CHIESTA"
        return voce
    # 5 · the probe: was the fault put in?  ⛔ and it is redone at every arm
    s = B76.sonda_gira()
    B76.stampa_sonda(s)
    passa_g, perche_g = B76.p_guasto_messo(nome_profilo, verifica, s)
    (_ok if passa_g else (_dub if passa_g is None else _ko))(
        "THE FAULT WAS PUT IN: %s" % perche_g)
    voce["sonda"] = s
    voce["guasto"] = {"passa": passa_g, "perche": perche_g}
    # 6 · the run
    usc = B76.scena_accendi("barra")
    if not usc:
        _ko("the scene does not start: I do NOT judge this cell")
        voce["esito"] = "LA SCENA NON E' PARTITA"
        return voce
    prima = B76.conti_qdisc()
    # ⛔ The trigger session must have FINISHED closing, or its «final
    #    count» falls into the window of this run (⇒ `registro_posato`).
    n0 = registro_posato()
    riga0 = B76.righe_registro()
    n = B70.giro("%s-%s" % (nome_profilo, etichetta), "barra",
                 B70.TELA_PIENA, secondi)
    if not conto_e_mio(n0, n):
        _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
    B76.scena_spegni()
    dopo = B76.conti_qdisc()
    # 7 · the counters around the run and the `rete-quic` lines
    delta = {k: dopo[k] - prima[k] for k in prima} if (prima and dopo) else None
    voce["qdisc"] = delta
    quic = leggi_rete_quic(riga0)
    voce["quic"] = quic
    B70.stampa_giro(n)
    # ⛔⭐ THE SAFETY NET OF `09-b70` IS USED, NOT BYPASSED: it is the predicate
    #    that refuses to say anything about the server side when the log is not
    #    from this run — that is the only thing that would have caught by itself the
    #    defect of the badly wrapped `root`.
    # ⚠ And we declare what it protects: K′ and F′ do NOT go through here (they live on the
    #   client's §11.1 trace), so a red of its own does not touch the verdict —
    #   it marks as not judgeable the four CORROBORATION numbers
    #   (`delta_non_spedito`, `chiave_aspetta`, `non_spediti`, `abbandonati`).
    if hasattr(B70, "p_registro_letto"):
        pr, perche_pr = B70.p_registro_letto(n)
        (_ok if pr else (_dub if pr is None else _ko))(
            "the log is from THIS run (§1.9): %s" % perche_pr)
        voce["registro_letto"] = {"passa": pr, "perche": perche_pr}
    _inf("QDISC   around the run: %s" % json.dumps(delta))
    stampa_rete_quic(quic)
    # ⛔ The lock of §8.2: if the slot was taken, this cell is not
    #    a measurement of the cure — it is a measurement of thirty seconds of lock.
    coda = ULTIMO_CLIENTE["testo"] or (n.get("coda_cliente") or "")
    if "GIA_ATTIVA" in coda or "0x0f" in coda.lower():
        _dub("⚠ the client found the slot TAKEN (§8.2 reason 0x0F): "
             "this cell does not measure the cure")
        voce["esito"] = "IL POSTO ERA OCCUPATO"
    voce["giro"] = n
    voce["staccato_dal_cliente"] = ("I did NOT stay attached" in coda)
    return voce


def appaia(a):
    _log("09-b79 · THE TWO CURES PAIRED — port %d · dev «%s»" % (PORTA, DEV))
    print("   ⛔ «%s» (ssh + the user's session) is NOT touched" % VIETATA)
    print("   ⛔ 7900/7910/7920/7930/7932 belong to others: they are COUNTED, not touched")
    md5 = md5_binario()
    print("   ⭐ the binary I measure: md5 %s (working tree, not HEAD)" % md5)
    print("   --  «%s» before: %s" % (DEV, RETE.qdisc() or "(none)"))

    if not B76.spedisci_sonda():
        _ko("the scripts were not written in %s" % LAV)
        return 2
    if B76.scegli_porta_sonda() is None:
        _ko("⛔ none of my probe ports is free: I do NOT measure, "
            "because without the probe I do not know whether the fault was put in")
        return 2
    _ok("the probe and the reader are in %s · the probe will use port %d"
        % (LAV, B76.PORTA_SONDA))
    prima_vicini = vicini_non_miei()
    _inf("attached to the ports NOT mine, BEFORE: %s"
         % json.dumps(prima_vicini, ensure_ascii=False))

    nomi = [x.strip() for x in a.profili.split(",") if x.strip()]
    if a.solo:
        nomi = [n for n in nomi if a.solo in n]
    scelti = []
    for nome in nomi:
        p = profilo(nome)
        if not p:
            _ko("the profile «%s» does not exist in 09-b76" % nome)
            return 2
        scelti.append(p)
    if not scelti:
        _ko("no profile chosen")
        return 2
    bracci = [b for b in BRACCI if b[0] in a.bracci]
    _inf("%d profiles × %d arms = %d cells of %d s"
         % (len(scelti), len(bracci), len(scelti) * len(bracci), a.secondi))

    CHI = "09-b79"
    AFFITTO = 900
    try:
        LUC.prendi(CHI, secondi=AFFITTO, attesa=a.attesa)
    except Exception as e:
        _ko("⛔ I DO NOT MEASURE: %s" % e)
        return 2
    scadenza = time.time() + AFFITTO

    esiti = []
    RETE.guardiano_arma(min(7200, len(scelti) * len(bracci) * (a.secondi + 90) + 900))
    try:
        for p in scelti:
            nome, regole, _pieno, _spir, _senza, perche, verifica = p
            if time.time() > scadenza - 400:
                if B76.rinnova(CHI, AFFITTO):
                    scadenza = time.time() + AFFITTO
                    _inf("⛔ lock lease renewed for %d s" % AFFITTO)
                else:
                    _ko("⛔ the lock is no longer mine: I STOP")
                    break
            _log("PROFILE «%s» — %s" % (nome, perche[:110]))
            casella = {}
            for etichetta, opzioni, soglia, ritmo, perche_b in bracci:
                _log("  %s · arm %s — %s" % (nome, etichetta, perche_b[:100]))
                v = una_casella(nome, regole, verifica, etichetta, opzioni,
                                soglia, ritmo, a.secondi)
                esiti.append(v)
                casella[etichetta] = v.get("giro") or {"esito": v.get("esito", "?")}

            # ── the predicates of the PAIR, and each one says its why ────────
            _log("  %s · THE PAIR" % nome)
            A = casella.get("A") or {}
            for et in ("B", "C"):
                if et not in casella:
                    continue
                passa, q = p_spirale_spenta(A, casella[et], et)
                (_ok if passa else (_dub if passa is None else _ko))(
                    "K′ · the cure switches off the spiral (%s): %s" % (et, q))
                passa2, q2 = p_ritmo_restituito(A, casella[et], et)
                (_ok if passa2 else (_dub if passa2 is None else _ko))(
                    "F′ · the cure gives back rhythm (%s): %s" % (et, q2))
                esiti.append({"profilo": nome, "coppia": et,
                              "K": {"passa": passa, "perche": q},
                              "F": {"passa": passa2, "perche": q2}})
            if nome == "ritardo-30" and len(casella) == 3:
                passa, q = p_linea_sana(casella)
                (_ok if passa else (_dub if passa is None else _ko))(
                    "⛔⛔ S′ · the cure must NOT cost on the healthy line: %s" % q)
                esiti.append({"profilo": nome, "linea_sana":
                              {"passa": passa, "perche": q}})
    finally:
        B76.scena_spegni()
        _log("⛔ THE NETWORK IS PUT BACK AS IT WAS")
        rimessa = RETE.rimetti()
        LUC.molla(CHI)

    os.makedirs(FUORI, exist_ok=True)
    dove = os.path.join(FUORI, "09-b79-esiti.json")
    with open(dove, "w") as f:
        json.dump({"md5_binario": md5, "esiti": esiti,
                   "vicini_prima": prima_vicini,
                   "vicini_dopo": vicini_non_miei()}, f,
                  ensure_ascii=False, indent=1)
    _inf("outcomes in %s" % dove)
    dopo_vicini = vicini_non_miei()
    _inf("attached to the ports NOT mine, AFTER: %s"
         % json.dumps(dopo_vicini, ensure_ascii=False))
    tabella(esiti)
    rossi = [e for e in esiti
             if any((e.get(k) or {}).get("passa") is False
                    for k in ("K", "F", "linea_sana"))]
    if not rimessa:
        _ko("⛔ the network did NOT go back as it was: put it back by hand with «rimetti»")
        return 2
    return 1 if rossi else 0


def tabella(esiti):
    """⛔ §6.2: ALL the quantities are printed.  ⭐ And the DRIFT sits next to the
       frames/s on every line, because a cure that doubles the rhythm and
       triples the delay is not obviously an improvement — and it is a
       choice that belongs to the user, not to this bench."""
    _log("THE THREE-ARM TABLE — ⚠ and the price (the drift) sits next to the "
         "gain")
    print("  %-14s %-2s %7s %7s %7s %7s %8s %8s %9s"
          % ("profile", "ar", "fps", "worst", "keyfr%", "drift", "driftMx",
             "Mbit/s", "cwnd_min"))
    for e in esiti:
        n = e.get("giro")
        if not n:
            continue
        if not B70._ha_misurato(n):
            print("  %-14s %-2s   %s" % (e["profilo"], e["braccio"],
                                         (n.get("esito") or "?")[:70]))
            continue
        q = e.get("quic") or {}
        print("  %-14s %-2s %7.2f %7s %6.1f%% %7s %8s %8s %9s"
              % (e["profilo"], e["braccio"], n["fps"], n["fps_finestra_min"],
                 (1 - n["quota_delta"]) * 100, n["deriva_fine_ms"],
                 n["deriva_max_ms"], n["mbit_s_filo"], q.get("cwnd_min")))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE `stacco` STEP — «WHO» detached on `raffica-forte`
# ═══════════════════════════════════════════════════════════════════════════
def stacco(a):
    """⛔ It does not deduce: it asks four independent witnesses (see
       the header).  ⚠ And the third possibility — «it never opened» —
       is ruled out EXPLICITLY, because it looks the same as detaching."""
    _log("09-b79 · `raffica-forte` — ⛔ WHO DETACHED?")
    p = profilo("raffica-forte")
    md5 = md5_binario()
    print("   ⭐ binary md5 %s · netem profile: %s" % (md5, " ".join(p[1])))

    # ⭐ The first witness is read in the SOURCE, before running: `IDLE_MS`.
    rc, out, _ = root("bash -c \"grep -n 'IDLE_MS' %s/src/trasporto.c | head -4\""
                      % ALB)
    _inf("`[R]` src/trasporto.c: %s" % " | ".join(out.split()))

    if not B76.spedisci_sonda() or B76.scegli_porta_sonda() is None:
        _ko("the scripts or the probe port are missing")
        return 2

    CHI = "09-b79-stacco"
    try:
        LUC.prendi(CHI, secondi=900, attesa=a.attesa)
    except Exception as e:
        _ko("⛔ I DO NOT MEASURE: %s" % e)
        return 2
    RETE.guardiano_arma(1800)
    fuori = {}
    try:
        RETE.rimetti(dillo=False)
        ok, righe = riavvia("", 0, False)
        if not ok:
            _ko("arm A is not in force: %s" % righe)
            return 2
        if not B70.innesca_sessione():
            _ko("the trigger session does not open (on a CLEAN network)")
            return 2
        _ok("⭐ on a CLEAN network the session opens: what follows belongs to the fault")
        passa_r, perche_r, riletta = installa_profilo(p[1])
        (_ok if passa_r else _ko)("the rule: %s" % perche_r)
        if not passa_r:
            return 2
        s = B76.sonda_gira()
        B76.stampa_sonda(s)
        passa_g, perche_g = B76.p_guasto_messo("raffica-forte", p[6], s)
        (_ok if passa_g else (_dub if passa_g is None else _ko))(
            "THE FAULT WAS PUT IN: %s" % perche_g)
        fuori["sonda"] = s

        usc = B76.scena_accendi("barra")
        if not usc:
            _ko("the scene does not start")
            return 2
        n0 = registro_posato()      # ⛔ see `registro_posato`
        riga0 = B76.righe_registro()
        t0 = time.time()
        n = B70.giro("stacco-raffica-forte", "barra", B70.TELA_PIENA, a.secondi)
        if not conto_e_mio(n0, n):
            _dub("⚠ %s" % (n.get("server") or {}).get("conto_dubbio"))
        B76.scena_spegni()
        B70.stampa_giro(n)
        fuori["giro"] = n
        fuori["quic"] = leggi_rete_quic(riga0)
        stampa_rete_quic(fuori["quic"])

        # ── WITNESS 1 · THE CLIENT, which says it by itself ────────────────
        _log("WITNESS 1 · the client (`01-b3-cliente.py:1979`)")
        coda = ULTIMO_CLIENTE["testo"] or (n.get("coda_cliente") or "")
        print("   ┌─ the client, IN FULL (⛔ not its last 400 bytes) ─")
        for r in coda.splitlines():
            if r.strip() and "tput:" not in r:
                print("   │ %s" % r[:160])
        print("   └─")
        attaccato = "still attached after" in coda
        staccato = "I did NOT stay attached" in coda
        fuori["cliente"] = {"attaccato_fino_in_fondo": attaccato,
                            "staccato": staccato, "coda": coda}
        if attaccato:
            _ok("⭐⭐ THE CLIENT SAYS THE SESSION DID **NOT** DETACH: it "
                "stayed attached for all the %d s requested" % a.secondi)
        elif staccato:
            _ko("⛔ the client says it dropped — and it also says why")
        else:
            _dub("the client said neither one thing nor the other")

        # ── WITNESS 2 · THE SERVER LOG ─────────────────────────────────────
        _log("WITNESS 2 · the server log — the farewell reasons")
        cercati = ("congedo motivo=", "the client takes its farewell", "slot DENIED",
                   "BANNED", "SILENZIO", "final count", "closing",
                   "GIA_ATTIVA", "idle", "expired")
        fuori["registro"] = {}
        for c in cercati:
            rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                              "-i '%s' | tail -3\"" % (riga0 + 1, LAV, c))
            righe = [x[:200] for x in out.splitlines() if x.strip()]
            fuori["registro"][c] = righe
            if righe:
                for r in righe:
                    _inf("«%s» → %s" % (c, r))
        if not any(fuori["registro"][c] for c in
                   ("congedo motivo=", "the client takes its farewell", "slot DENIED",
                    "BANNED", "GIA_ATTIVA")):
            _ok("⭐ NO farewell, NO slot denied, NO ban in the whole "
                "run: on the server side nobody detached")

        # ── WITNESS 3 · THE HANDSHAKE — the third possibility ──────────────
        _log("WITNESS 3 · ⚠ «it never opened» looks the same as "
             "«it detached»")
        aperta = "SESSIONE" in coda or (n.get("fotogrammi_grezzi") or 0) > 0
        rc, out, _ = root("bash -c \"tail -n +%d %s/registro.log | grep -a "
                          "'AMMESSO\\|ATTACCA\\|session open\\|monitor «' | "
                          "head -5\"" % (riga0 + 1, LAV))
        for r in out.splitlines()[:5]:
            _inf("opening: %s" % r[:180])
        fuori["apertura"] = {"aperta": aperta, "righe": out.splitlines()[:5]}
        if aperta:
            _ok("⭐ THE SESSION OPENED (the hypothesis «the handshake does not "
                "complete» is ruled out): `09-b78-apertura.py` had already "
                "measured it up to 25 %% loss, 10 runs out of 10 in ~1.3 s")
        else:
            _ko("⛔ the session NEVER opened: it is not a detach")

        # ── WITNESS 4 · THE WINDOW, and the server's count ─────────────────
        _log("WITNESS 4 · the congestion window and the server counts")
        srv = (n.get("server") or {})
        _inf("SERVER  %s" % json.dumps(srv, ensure_ascii=False)[:600])
        q = fuori["quic"]
        if q.get("esito") == "letto":
            _inf("⭐ the window: cwnd min %s, median %s, end %s · judgements %s"
                 % (q["cwnd_min"], q["cwnd_mediana"], q["cwnd_fine"],
                    json.dumps(q["giudizi"], ensure_ascii=False)))
        fuori["secondi_veri"] = round(time.time() - t0, 1)
    finally:
        B76.scena_spegni()
        RETE.rimetti()
        LUC.molla(CHI)

    os.makedirs(FUORI, exist_ok=True)
    dove = os.path.join(FUORI, "09-b79-stacco.json")
    with open(dove, "w") as f:
        json.dump(fuori, f, ensure_ascii=False, indent=1)
    _inf("outcomes in %s" % dove)

    # ── THE VERDICT, and the right word ────────────────────────────────────
    _log("THE VERDICT on `raffica-forte`")
    n = fuori.get("giro") or {}
    if fuori.get("cliente", {}).get("attaccato_fino_in_fondo"):
        _ok("⭐⭐⭐ NOBODY DETACHED.  The connection stayed alive for "
            "all the %d s; what stopped was the DELIVERY OF FRAMES after "
            "%s s.  ⇒ The red of `09-b76` is true as a number and WRONG as a "
            "word: `p_niente_stacco` measures how long delivery lasted, not "
            "whether the connection dropped.  ⛔ And the fact stays serious — a "
            "session alive and MUTE is a frozen screen — but it has another name and "
            "another cause." % (a.secondi, n.get("vissuto_s")))
        return 0
    if fuori.get("cliente", {}).get("staccato"):
        _ko("⛔ THE CLIENT DROPPED: %s" % fuori["cliente"]["coda"][-300:])
        return 1
    _dub("none of the witnesses answered: I have nothing to judge")
    return 3


# ═══════════════════════════════════════════════════════════════════════════
def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", nargs="?",
                   choices=["terreno", "appaia", "stacco", "rimetti", "stato"])
    p.add_argument("--certifica", action="store_true",
                   help="⭐ the positive control: it does not touch the machine")
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="one profile only, by name")
    p.add_argument("--bracci", default="ABC")
    p.add_argument("--profili", default=("ritardo-30,perdita-1,perdita-3,"
                                         "jitter-15,jitter-30,casa-cattiva,"
                                         "raffica-forte"))
    p.add_argument("--attesa", type=int, default=3600,
                   help="how many seconds I wait for the netem lock")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if not a.passo:
        p.error("a step is needed, or --certifica")

    importa()
    if a.passo in ("rimetti", "stato"):
        _log("the test machine's network — dev «%s», port %d" % (DEV, PORTA))
        _inf("attached to the ports NOT mine: %s"
             % json.dumps(vicini_non_miei(), ensure_ascii=False))
        return 0 if RETE.rimetti() else 2
    if a.passo == "terreno":
        ok = B76.spedisci_sonda()
        _inf("binary md5 %s" % md5_binario())

        return 0 if (B70.terreno_controlla() and ok) else 2
    if a.passo == "stacco":
        return stacco(a)
    return appaia(a)


if __name__ == "__main__":
    sys.exit(principale())
