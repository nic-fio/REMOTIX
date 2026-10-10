from build import arrow, box, c, code, fig, note, p, rif, seq, table, text, tip, ul, warn, zone

# ── 1. The quality contract ────────────────────────────────────────────────
S1 = p("REMOTIX does not chase a bitrate or a quality score. It follows a short contract written by the user "
       "in " + c("SPECIFICHE.md") + " §3 and §8 and in " + c("DECISIONI.md") + " §2–§4: what may be spent "
       "when there is not enough, in which order, and what must never be spent. Every mechanism of this "
       "chapter exists to keep one line of that contract, and each one says so in the log.", lead=True) + \
    table(["Rule", "What it says", "Where it is enforced"], [
        ["<b>I1 — the rate falls only on measure</b>", "The frame rate never drops out of prudence, to save "
         "bandwidth or because the scene is still. It drops only when a measurement proves the line does not "
         "carry, and every drop is written in the log next to the number that caused it.",
         "The rate regulator, the quality ladder, the decoder-queue skip in the page"],
        ["<b>Degrade in time, not in space</b>", "Below the minimum, frames are dropped; the image is never "
         "made coarse on purpose and the session is never cut (§3.3). A slow but sharp desktop can still be read.",
         "QP fixed by default; the ladder moves only on the 16 MiB cap"],
        ["<b>Artefacts yes, fluidity and sync no</b>", "Below the declared floor, the product may lose sharpness "
         "and detail; it may not lose smooth motion or audio/video sync (§4.6-decies, 25 Aug 2026).",
         "The audio is never sacrificed to the video; key requests are paced"],
        ["<b>A dead line is called dead</b>", "A line that no longer carries anything is not a slow line: the "
         "connection is closed and the user signs in again by hand (§3.1-quater).", rif("The dead line")],
        ["<b>Full means refuse, with the reason</b>", "When the machine has no capacity left, a newcomer is "
         "refused with " + c("BUDGET_PIENO") + " before any desktop is started; those already working are "
         "never slowed down to make room (§4.6-bis).", rif("Admission: the session cap and the budget")],
    ], "«TAB» — The rules that every quality mechanism serves") + \
    table(["Number", "Value", "Status"], [
        ["Minimum image", "480p · 25 frames/s · 24 bit", "A guarantee: the bottom of the degradation ladder, not a target"],
        ["Desired image", "4K · 60 frames/s · 10 bit per channel", "A design goal. The shipped stream is H.264 High, "
         "8 bit (see " + rif("Video encoding") + "); the capture asks for 60 frames/s (" + c("MOVIMENTO_FPS") + ")"],
        ["Latency of our piece", "cap 50 ms, target 40 ms, from input arrival to frame departure",
         "A design goal; the network is not counted because it is not ours"],
        ["Network floor", "30 Mbit/s", "A declared premise: below it nothing is promised, but nothing is cut either"],
    ], "«TAB» — The numbers of SPECIFICHE.md §3 and §8") + \
    note("since 30 September 2026 the thresholds of " + c("SPECIFICHE.md") + " §3 are design goals, not "
         "measured promises: the user removed the performance tests from the acceptance criteria as too "
         "hardware-dependent. Parameters the product really uses (floor, session cap, clocks) are configuration "
            "and hold as written.", "Goals, not promises.") + \
    p("The floor was 20 Mbit/s on the morning of 23 August 2026 and became 30 the same night (§3.1-sexies). "
      "Phase 9 was calibrated on 20, and its numbers were left as measured; the encoder's bandwidth cap "
      "still derives its three numbers from the value passed on the command line, so the operator chooses "
      "which floor it represents (" + rif("Encoder rate control") + "). The user then moved the target of "
      "the phase: bandwidth is a premise, the real challenge is a line that <i>loses, reorders and jitters</i> "
      "(§3.1-ter). Most of the mechanisms below react to queues, not to Mbit/s.")

# ── 2. Where quality is decided ───────────────────────────────────────────
DOVE = fig(
    zone(20, 12, 200, 250, "Child process (per user)")
    + zone(240, 12, 200, 250, "Parent: main loop")
    + zone(460, 12, 200, 250, "Parent: WebTransport")
    + zone(680, 12, 200, 250, "Browser page")
    + box(32, 44, 176, 50, "Capture", "60 frames/s requested", "blue")
    + box(32, 114, 176, 50, "Encoder", "QP 26 · 16 MiB ladder", "navy")
    + box(32, 184, 176, 50, "Quality rise · bit cap", "off by default", "grey")
    + box(252, 44, 176, 50, "deposita_fotogramma()", "every frame of every child", "blue")
    + box(252, 114, 176, 50, "Budget accumulator", "budget_deposita()", "amber")
    + box(252, 184, 176, 50, "Admission", "cap · budget · verdict", "amber")
    + box(472, 44, 176, 50, "Rate regulator", "ritmo_frena()", "navy")
    + box(472, 114, 176, 50, "Queue threshold", "video_sgombra(), 100 ms", "navy")
    + box(472, 184, 176, 50, "Dead line", "stall 5 s · silence 10 s", "navy")
    + box(692, 44, 176, 50, "Stream reader", "FIN or RESET, open order", "blue")
    + box(692, 114, 176, 50, "Gap rule", "one key request per gap", "blue")
    + box(692, 184, 176, 50, "Decoder queue skip", "only if drawing is the bottleneck", "light")
    + arrow(120, 96, 120, 112) + arrow(210, 130, 250, 76)
    + arrow(340, 96, 340, 112) + arrow(340, 166, 340, 182)
    + arrow(430, 69, 470, 69) + arrow(560, 96, 560, 112)
    + arrow(650, 139, 690, 80) + arrow(780, 96, 780, 112)
    + arrow(780, 166, 780, 182),
    900, 270, "«FIG» — Where each quality and capacity mechanism lives; frames flow left to right")

S2 = p("Quality is not decided in one place. The encoder lives in the per-user child process, the budget "
       "and the admission in the parent's main loop, the line-facing regulators in the parent's WebTransport "
       "layer, and the last word — what reaches the screen — in the page. Each piece decides only on what it "
       "can measure locally.", lead=True) + DOVE + \
    table(["Mechanism", "Option (default)", "Process / file", "What it changes"], [
        "Line-facing cures (phase 9, on by default since 24 Aug 2026)",
        ["Video queue threshold", c("--sgombra-soglia-ms N") + " (100; 0 = off)", "parent · " + c("src/webtransport.c"),
         "A delta stuck in our queue is abandoned only if the queue cannot drain within N ms"],
        ["Rate regulator", c("--niente-ritmo-adattivo") + " turns it off (on)", "parent · " + c("src/webtransport.c"),
         "A frame is not sent while 2 deltas still have bytes in our queue"],
        ["Dead line", c("--niente-linea-morta") + " (on); " + c("--linea-morta-stallo-ms N") + " (5000); "
         + c("--linea-morta-silenzio-s N") + " (10)", "parent · " + c("src/webtransport.c"),
         "Closes the connection when the line no longer carries"],
        ["Ghost eviction", c("--sfratto-ms N") + " (15000; 0 = off)", "parent · " + c("src/rcp.c"),
         "A silent client of the same user loses its seat to a newcomer of that user"],
        ["Audio silence", c("--niente-audio-silenzio") + " turns it off (on)", "child · " + c("src/audio.c"),
         "An all-zero audio block is not sent"],
        "Encoder cures (phase 9, off by default: the user has not judged them)",
        ["Quality rise", c("--qualita-risale") + " (absent = off)", "child · " + c("src/codificatore.c"),
         "After the 16 MiB ladder bit, climbs back one step at a time"],
        ["Bandwidth cap", c("--tetto-banda-mbit N") + " (0 = off)", "child · " + c("src/codificatore.c"),
         "Switches the encoder from constant QP to QVBR with a ceiling"],
        "Capacity (phase 10)",
        ["Composition budget", c("--budget-mpixel-s N") + " (0 = off)", "parent · " + c("src/budget.c"),
         "Refuses a newcomer with 0x06 when the machine has no composition capacity left"],
        ["Reserve fraction", c("--riserva F") + " (0.5)", "parent · " + c("src/budget.c"),
         "How much of an idle tenant's worst case is kept aside"],
        ["Session cap", c("--tetto-sessioni N") + " (10)", "parent · " + c("src/rcp.c") + ", " + c("src/main.c"),
         "Administrative limit; refused with 0x0E"],
    ], "«TAB» — Every quality and capacity switch, its default and where it lives") + \
    p("Two of these live in the child, which is a separate program started with " + c("execve") + " and a "
      "freshly composed environment: they cannot travel as environment variables. " + c("figli_fase9()")
      + " (the phase 9 settings for the children) stores them and the child's command line carries " + c("--qualita-risale") + " and "
      + c("--tetto-banda-mbit") + " (and the audio-silence switch) when it is built. Every switch writes its "
      "value in force at startup, <i>on and off</i>: “switched off” and “never had to act” must not look the "
      "same in the log.") + \
    note("each cure has exactly one way to be switched off. The old enabling names " + c("--ritmo-adattivo")
         + " and " + c("--linea-morta") + " no longer exist: typing them prints an explanation and exits with "
         "status 2. The temporary environment bridge for the queue threshold was removed on 23 August 2026 "
         "when the option arrived: two ways to set the same value are two numbers that can diverge.",
         "One way per switch.")

# ── 3. Encoder rate control ───────────────────────────────────────────────
S3 = p("By default the encoder runs at a <b>constant QP of 26</b> (" + c("QP_HARDWARE") + " in "
       + c("src/figlio.c") + ", mode " + c("CODIFICATORE_QUALITA_QP") + "), with no bitrate, no buffer and "
       "no rate controller. With " + c("--tetto-banda-mbit N") + " it switches to <b>QVBR</b>, a rate "
       "controller with a ceiling in which the QP still acts as the quality factor.", lead=True) + \
    p("Constant QP is the direct translation of I1 and of “never coarsen”: the quantiser is fixed, so the "
      "image of a quiet desktop never gets worse, and the bandwidth is simply what comes out. Measured on the "
      "test machine on 23 August 2026 (2560×1080, " + c("EncSliceLP") + " on the Intel UHD 770, QP 26, 30 s "
      "per point), the real desktop of the user moving at full screen cost <b>0.204 Mbit/s</b>; a film with "
      "grain at full screen cost <b>58.7 Mbit/s</b>. (The phase 9 document later found that this series had "
      "been taken with the test client negotiating HEVC; re-measured in H.264 the same night, the hard case "
      "still asked 44.6 Mbit/s.) A cap that bit on ordinary content would repeat the mistake that cost v1 a "
      "whole phase, so the cap is for the hard case only, and it is off until the user judges it.") + \
    table(["Mode", "Still scene", "Hard scene (noise)", "Verdict"], [
        ["CQP 26", "0.193 Mbit/s", "259.9 Mbit/s", "the default: no ceiling at all"],
        ["CBR 16M", "15.98 Mbit/s", "15.99 Mbit/s", "out: 83× the CQP cost on a still screen, for nothing"],
        ["VBR 12/16M with qp=26", "0.686", "11.13", "out: <b>the qp is ignored</b> — byte-identical output with and without it"],
        ["VBR 12/16M without qp", "0.686", "11.13", "(the proof of the line above)"],
        ["<b>QVBR 12/16M, qp=26</b>", "<b>0.218</b>", "<b>11.14</b>", "chosen: the ladder still acts, the ceiling holds"],
    ], "«TAB» — Rate-control modes measured on 23 Aug 2026 on the development laptop (same Intel iHD 25.2.3 "
       "driver as the test machine, different GPU), 2560×1080, 25 frames/s, 6 s") + \
    p("Under VBR the QP is silently ignored, which would turn the quality ladder and the quality rise into "
      "no-ops: a component that ignores an option without saying so is precisely the failure this file exists "
      "to avoid. The three numbers of the cap are <b>derived</b> from the floor given on the command line, never "
      "written by hand (" + c("tetto_filo()") + " (wire), " + c("tetto_punto()") + " (working point), "
      + c("tetto_serbatoio_bit()") + " (buffer in bits)):") + \
    table(["Number", "Rule", "At 20 Mbit/s", "Why"], [
        ["Wire (max rate)", c("TETTO_QUOTA_FILO") + " = 80 % of the floor", "16 Mbit/s",
         "Measured: with zero video, audio, input, clipboard and QUIC overhead take 2.4 Mbit/s; 16 + 2.4 = 92 % of the floor"],
        ["Working point (target rate)", c("TETTO_QUOTA_PUNTO") + " = 75 % of the wire", "12 Mbit/s",
         "<b>Never equal to the wire</b>: with the two equal, the Intel driver silently deduced CBR in v1 (lesson R31)"],
        ["Buffer (VBV)", c("TETTO_VBV_MS") + " = 40 ms of the wire", "640 kbit",
         "The 40 ms target of our piece, not the 50 ms cap. v1 used " + c("bit_rate / 2") + ", which is half a <i>second</i>"],
    ], "«TAB» — The three numbers of the bandwidth cap, derived from the floor") + \
    p("The mode is <b>asked for by name</b> (" + c("modo_bitrate_voluto()") + ", the wanted bitrate mode) and checked against the mask the "
      "driver declares: on VA-API the declared rate-control bits are read with " + c("vaGetConfigAttributes")
      + " and printed in clear, and a mode the driver does not declare makes the encoder fail loudly instead "
      "of falling back to a mode nobody chose. " + c("tetto_in_tre_numeri()") + " (the cap in three numbers) refuses a working point "
      "not below the wire and a non-positive buffer, and " + c("serbatoio_entro_i_50_ms()") + " (buffer within 50 ms) refuses a buffer "
      "longer than 50 ms. On Vulkan Video, which has no QVBR, the cap becomes VBR with the requested QP as the "
      "floor of the controller (" + c("apri_scheda_vulkan()") + ", which opens the Vulkan encoder); without the cap the card must declare CQP.") + \
    warn("the cap applies only to hardware encoding — since phase 19 there is no other kind — and the value "
         "passed is a <i>floor</i>, not a ceiling. The code comments and the phase 9 measurements use 20 Mbit/s; "
         "the declared product floor is 30 (" + c("DECISIONI.md") + " §3.1-sexies). Whoever switches the cap on "
         "chooses which one to pass.", "Which floor.") + \
    p("Not settled yet: the cap and the quality rise are off by default and await the user's judgement on "
      "the real desktop; " + c("max_frame_size") + ", which QVBR would accept, is deliberately not used — a second "
      "lever on the same quantity would give two measurements under one label.")

# ── 4. The 16 MiB cap and the quality ladder ─────────────────────────────
S4 = p("RCP.md §6.2 forbids a video frame larger than 16 MiB: the sender must re-encode it at a lower quality "
       "and log it, never send it. That rule is the only thing that moves the QP of a running encoder.",
       lead=True) + \
    p("When a frame comes out of the card above " + c("TETTO_FOTOGRAMMA") + " (the frame ceiling, 16 777 216 "
      "bytes), " + c("comprimi_comune()") + " (the shared compression path) logs it, records the step on which the cap bit (" + c("qualita_fallita") + "), "
      "and " + c("abbassa_qualita()") + " (lower the quality) raises the QP by " + c("CRF_PASSO") + " (the step) = 9, capped at 51. Changing "
      "quality closes and reopens the card context (" + c("cambia_qualita()") + ", change the quality), so the next frame is "
      "always a <b>keyframe</b>. The ladder from the default is therefore 26 → 35 → 44 → 51.") + \
    table(["Frame", "How far down", "If it still does not fit"], [
        ["Keyframe", "The whole ladder: a keyframe may not be abandoned (RCP.md §5.2)",
         "At 51 it is not sent, and the log says “nothing left to lower”"],
        ["Delta", c("RICODIFICHE_MASSIME") + " (maximum re-encodings) = 3 encodings in total: 26, 35, 44 — two descents, both tried",
         "Abandoned. The reopened context makes the next frame a keyframe, so the client never loses its reference"],
    ], "«TAB» — How a frame over the cap is handled") + \
    p("The step was 6 until 22 August 2026, and it was one step short: at 7680×4320 with almost incompressible "
      "content a keyframe was 16.654 MiB at QP 38 (104 % of the cap, eight times out of eight) and 11.056 MiB at "
      "QP 44. Each attempt costs 91–108 ms in hardware at 8K, so a wider step is cheaper than an extra attempt. "
      "The limit was later lowered to 4096×2304 (see " + rif("Canvas and view") + "), and at the user's own "
      "canvas the largest of 404 real keyframes was 21 433 bytes, 0.13 % of the cap: the ladder is a safety net "
      "for exceptional frames, not a working mechanism. The encoder side of the same mechanism is in "
      + rif("Frame ceiling and quality steps") + ".") + \
    p("Every descent is declared in the log (area " + c("video") + ") with the frame size and its percentage of "
      "the cap. A percentage of 100 or less would be a descent out of prudence, which I1 forbids, and the line "
      "would prove it on its own.") + \
    note("until 23 August 2026 the delta branch was dead code: the counter read " + c("prossimo_chiave")
         + " (next frame is a key) inside the loop, and every reopen set it, so a delta always walked the whole ladder while the "
         "startup line claimed it stopped after three attempts. The frame's kind is now decided once, before "
         "the first descent (" + c("chiave_chiesta") + ", key requested).", "A dead branch, fixed.")

# ── 5. Quality recovery ────────────────────────────────────────────────────
S5 = p("Before phase 9 the QP was a ratchet: four writes, all downwards. One exceptional frame left the "
       "session at the bottom of the ladder for hours, with a quiet desktop permanently coarse and no log "
       "line saying why. " + c("--qualita-risale") + " adds the way back; it is off by default (invariant I6: "
       "what changes what the user sees stays behind a switch until the user has looked).", lead=True) + \
    table(["Constant", "Value", "Meaning"], [
        [c("RISALITA_MARGINE"), "2 MiB (one eighth of the cap)", "A frame counts as calm only if it is comfortably under the cap"],
        [c("RISALITA_ATTESA"), "120 frames (~2 s at 60/s)", "Calm frames in a row before climbing one step"],
        ["Back onto the failed step", "twice the wait", "The step where the cap bit is a measured fact, not a suspicion"],
        [c("RISALITA_ATTESA_MAX"), "3840 frames (~64 s)", "The wait doubles at every relapse and never comes back down"],
    ], "«TAB» — The numbers of the quality rise") + \
    p(c("risali_qualita()") + " (raise the quality) runs at the entry of the next frame, never with a packet in hand (closing the "
      "context frees its bytes). It climbs one step at a time and never above the quality the caller "
      "requested. A relapse right after a climb doubles the wait (" + c("risalito_da_poco") + ", recently raised). The two "
      "defences against flapping are the eighth-of-the-cap margin — a scene sitting at 95 % of the cap never "
      "produces a calm frame — and the doubling, which halves the reopen rate at every round. If the context "
      "does not reopen at the new value, it falls back to the old one: climbing is optional, and a cure that "
      "kills the session when it fails is worse than the defect.") + \
    p("Not settled yet: the three numbers are declared sufficient, not right; the phase 9 bench criteria "
      "(more than 3 reopens per minute, or a lower frame rate with the cure than without) would condemn them.")

# ── 6. The queue threshold ────────────────────────────────────────────────
S6 = p("Each video frame travels on its own unidirectional QUIC stream. When a newer frame is produced while an "
       "older delta still has bytes in <i>our</i> send queue, RCP.md §5.1 allows (it does not require) a "
       + c("RESET_STREAM") + " of the old one. " + c("video_sgombra()") + " (clear the video queue) decides when to use that permission.",
       lead=True) + \
    p("Until 23 August 2026 every older delta was abandoned at once. On the test machine, with a 3-second dip "
      "to 10 Mbit/s and a 1920×1080 scene, abandonments and keyframes went <b>one to one</b>, even on the wide "
      "line: each abandon opened a gap, each gap asked for a keyframe, and the abandoning itself was "
      "manufacturing keyframes. Since 24 August a delta is abandoned only if the video queue cannot drain "
      "within " + c("WT_SGOMBRA_SOGLIA_MS") + " = 100 ms:") + \
    code("""
wait_ms = video_queue_bytes * smoothed_rtt / cwnd       (from ngtcp2)
        = video_queue_bytes / 2500                      (fallback: no rtt/cwnd yet, 20 Mbit/s)
wait <= threshold            -> keep every delta (counted, one log line per state change)
wait >  threshold            -> abandon the live deltas still in our queue
wait >  threshold, a KEY in queue -> keep the deltas behind it (22 Sep 2026)
""", "text", "The decision of video_sgombra()") + \
    p("Only bytes still in our own queue are considered; what has already been handed to ngtcp2 is not taken "
      "back (nothing would be saved). The last rule was added on 22 September 2026 after a user test with a 4K "
      "video on KDE: a ~300 KB keyframe in the queue pushed the wait above the threshold on its own, abandoning "
      "the deltas behind it did not shorten it, but opened a gap, which requested another large keyframe — "
      "abandons climbed by one per keyframe, 7 → 13 in 6 s, and then the dead line fired. Behind a keyframe "
      "the deltas are kept, and braking production is left to the rate regulator.") + \
    p("The price, measured 23–24 August 2026 (bench 09-b79, together with the rate regulator): up to "
      "<b>+160 ms</b> of drift on a bad line, <b>zero</b> on a healthy one (39.85 / 40.19 / 39.63 frames/s in "
      "the three arms, no keyframes in any of them). " + c("--sgombra-soglia-ms 0") + " restores the old "
      "behaviour byte for byte.")

# ── 7. The rate regulator ─────────────────────────────────────────────────
S7 = p("The rate regulator is the only mechanism that lowers the frame rate, and it does so on a local fact: "
       "<b>" + c("arretrato") + "</b> (backlog), the number of live, non-key deltas that still have bytes in our send "
       "queue, read when a new frame arrives and before " + c("video_sgombra()") + ".", lead=True) + \
    p(c("ritmo_frena()") + " (rate brake) returns “do not send” when " + c("arretrato") + " reaches "
      + c("WT_RITMO_POSTI") + " (rate slots) = 2: one frame of overlap is allowed, two left behind are not. Nothing comes from outside — no loss "
      "rate, no reorder, no client silence can distort it — and there is no state to climb back: the quantity "
      "is re-read at every frame, so the episode ends by itself when the queue empties. Keyframes never pass "
      "through it; they have their own pacing (" + rif("Keyframe request pacing") + ").") + \
    table(["Fact", "Consequence"], [
        ["The threshold is its prerequisite", "With " + c("--sgombra-soglia-ms 0") + " the queue is emptied at every "
         "frame, " + c("arretrato") + " can never exceed 1, and the regulator never fires. The startup log says "
         "so explicitly when that combination is chosen"],
        ["It brakes downstream of the encoder", "The dropped frame was already encoded and the encoder's "
         "references moved on. Since 23 September 2026 a drop marks the stream as damaged ("
         + c("rcp_video_scartato_prima_del_filo()") + ") and requests a keyframe at once (" + c("video_regola()")
         + ", the only place that asks the stage for a key). Without it the client saw an image decaying into tiles with every counter green (27 and 38 "
         "drops, 0 gaps, 1 key in the session)"],
        ["One keyframe per episode", c("serve_chiave") + " (key needed) is a boolean cleared only when the key has left whole, "
         "and deltas behind that key are not abandoned"],
        ["Two log lines per episode", c("il ritmo SCENDE") + " (the rate goes down) with " + c("arretrato") + ", slots, queue bytes, "
         + c("cwnd") + ", " + c("cwnd_left") + ", bytes in flight, RTT and the queue inside the network ("
         + c("smoothed_rtt - min_rtt") + "); " + c("il ritmo RISALE") + " (the rate goes back up) with the duration. Never one line per frame"],
        ["One line per second while on", c("ritmo_ciclo()") + " (the once-a-second rate tick) prints how many times " + c("arretrato")
         + " was read: <i>zero reads</i> means a still scene, not “zero backlog”"],
    ], "«TAB» — What the regulator depends on and what it costs") + \
    p("Measured in the phase 9 paired comparison: keyframes dropped from 51.7–88.1 % of frames to 0.0–5.6 %, "
      "and the delivered rate rose 1.7–2.8× on the degraded profiles (" + c("DECISIONI.md") + " §3.1-septies). The "
      "price is the same +160 ms shared with the threshold.") + \
    warn("the congestion algorithm was never chosen: " + c("src/trasporto.c") + " calls "
         + c("ngtcp2_settings_default()") + " and keeps ngtcp2's default (CUBIC). On Wi-Fi a loss-based "
         "algorithm reads radio loss as congestion and halves the window, which manufactures exactly the backlog "
         "this regulator measures (" + rif("Congestion and the send queue") + "). Not settled yet: a different algorithm "
         "is to be tried as a separate experiment.",
         "Congestion control.") + \
    p("Not settled yet: " + c("WT_RITMO_POSTI") + " = 2 is to be calibrated; the falsifiable prediction is zero "
      "descents at 20 Mbit/s with a moving scene. The proper fix of the cost (stop <i>encoding</i> instead of "
      "dropping after encoding) needs the decision to reach the child, and is a second step.")

# ── 8. Keyframe pacing ────────────────────────────────────────────────────
S8 = p("A keyframe is about ten times a delta. Asking for one at every sign of trouble is the spiral that "
       "RCP.md §5.2 names: during a burst of losses the requests multiply and every keyframe worsens the "
       "condition that caused it. Both ends pace their requests.", lead=True) + \
    table(["Where", "Constant", "Value", "Rule"], [
        ["Page", "—", "1 per gap, re-asked after 1 s", c("Schermo.buco()") + " (Screen.gap): while a gap is open no second "
         "request is sent; if the key has not arrived after 1 s it is asked again (the server may ignore one)"],
        ["Server, RCP", c("V_GRAZIA_CHIAVE"), "200 ms", "A request within 200 ms of the last keyframe sent may be ignored"],
        ["Server, towards the child", c("WT_CHIAVE_RICHIESTA_MS"), "150 ms", "The floor between two requests to the capture process"],
        ["", c("WT_CHIAVE_MARGINE_PC"), "120 %", "Margin on the time the last key needs to leave: "
         + c("chiave_byte × rtt / cwnd")],
        ["", c("WT_CHIAVE_TETTO_MS"), "2000 ms", "The longest the image may stay broken: after that a key is asked anyway"],
        ["", c("WT_CHIAVE_DEBITO_TETTO_MS"), "1000 ms", "A second safeguard: while the key debt is on, every refused frame can re-ask, independently of the heartbeat"],
    ], "«TAB» — The pacing of keyframe requests") + \
    p(c("chiave_intervallo_ms()") + " first looks at a fact: if the previous keyframe still has bytes in our "
      "queue, the answer is the 2-second ceiling. Otherwise it computes, from ngtcp2's own " + c("cwnd")
      + " and smoothed RTT, how long a keyframe of the last size needs to leave, adds 20 %, and never goes below "
      "150 ms or above 2 s. Every change of the interval by 100 ms or more is logged with the bandwidth it was "
      "derived from.") + \
    table(["Scene (30 s, PCM audio)", "Interval", "Audio blocks before → after", "Video frames before → after"], [
        ["3 Mbit/s, still desktop", "150 (inert)", "6 009 → 6 002", "1 → 1"],
        ["15 Mbit/s, moving desktop", "150 (inert)", "4 076 · 3 944 → 3 984 · 3 830", "743 · 742 → 683 · 677"],
        ["3 Mbit/s, moving desktop", "~171 ms", "371 · 462 → 1 552 · 1 595 · 1 725", "115 · 99 → 89 · 128"],
        ["1 Mbit/s, moving desktop", "600–1000 ms", "15 → 577", "57 → 47"],
    ], "«TAB» — Bench 07-b65, 21 Aug 2026 evening, test machine, alternating runs differing by one line") + \
    p("Where there is bandwidth the cure declares itself inert (" + c("la banda misurata basta: resta il fondo di 150 ms")
      + ", “the measured bandwidth is enough: the 150 ms floor remains”, 100 times out of 101 at 15 Mbit/s). On a narrow line the image stays broken longer after "
      "a loss — that is the price, and it is visible — and in exchange the audio, whose datagrams found "
      + c("cwnd_left = 0") + " behind keyframes asked faster than they could leave, gets through.")

# ── 9. The dead line ──────────────────────────────────────────────────────
S9 = p("The fifth cure is of another kind: it does not decide how well the desktop is seen but whether the "
       "connection still exists. The user decided on 23 August 2026 that a line losing in bursts is not a slow "
       "line but a broken one: the wire drops and the user signs in again by hand.", lead=True) + \
    table(["Cause", "Condition", "Default"], [
        ["<b>Stall</b>", "No byte of video has left for N ms <i>while there was something to send</i> — bytes of frames "
         "still queued, or a new frame from the child. A still scene never starts the count", c("WT_LM_STALLO_MS") + " = 5000 ms"],
        ["<b>Silence</b>", "No packet from the client for N s, with at least " + c("WT_LM_MIN_PROVE") + " = 2 of our "
         "packets sent in the meantime", c("WT_LM_SILENZIO_S") + " = 10 s"],
    ], "«TAB» — The two causes of the dead line") + \
    p(c("linea_morta_giudica()") + " (judge the dead line) evaluates both from two monotonic local counters (video bytes handed to "
      "ngtcp2, frames offered by the child) and from ngtcp2's received-packet counter; time enters only as the "
      "distance between two samples. When either fires, " + c("linea_morta_scatta()") + " (fire the dead line) writes one line "
      "starting with " + c("linea-morta") + " that carries every number of the decision (" + c("causa=") + ", "
      + c("stallo_ms=") + ", " + c("silenzio_ms=") + ", " + c("prove=") + ", " + c("cwnd=") + ", " + c("ritmo_giu=")
      + " …), and the transport, the only owner of the QUIC connection, closes it. With the dead line on, the "
      "transport's PINGs move from 10 s to half the silence threshold (5 s), or “the client does not answer” "
      "and “we never asked” would look the same.") + \
    p("The stall threshold sits 5.0× above the longest empty second of " + c("raffica-1") + " (burst 1, a line that "
      "holds, 23.94 frames/s) and 2.9× below the 14.26 s freeze of " + c("raffica-forte") + " (strong burst, a line that serves "
      "nobody); on " + c("casa-cattiva") + " (bad home line), the worst line that holds for ten minutes, the stall never exceeded "
      "500 ms — a margin above 10× (measured 23–24 Aug 2026, test machine, " + c("netem") + " profiles). It is the "
      "most expensive cure: a wrong threshold would throw out someone who is working, so whoever touches "
      + c("WT_LM_STALLO_MS") + " must measure those two margins again.") + \
    warn(c("DECISIONI.md") + " §3.1-quater also lists “copious loss within 1–2 s” as a cause. The code does "
         "not: the loss fraction was refuted by its own bench on 23 August 2026 — " + c("casa-cattiva")
         + " declared 512‰ and held for ten minutes, " + c("raffica-forte") + " declared 123‰ and did not. On a "
         "reordering line " + c("pkt_lost/pkt_sent") + " measures reordering, not loss. The fraction stays in "
         "the log line as " + c("permille=") + ", a witness rather than a judge, and "
         + c("--linea-morta-permille") + " no longer exists.", "Loss is not a cause.") + \
    p("On the page the closed transport takes the session back to the login form with the sentence that the "
      "connection was interrupted and the password must be typed again (" + rif("End of session in the page")
      + "). At 10 % loss the cures do not save the experience — the user called it “stuck” — and declaring the "
      "line dead is the only honest answer (§3.1-septies). The transport side — PINGs, QUIC idle timeout, the "
      "closing itself — is in " + rif("Keep-alive, silence and the dead line") + ".")

# ── 10. Ghost eviction and audio silence ─────────────────────────────────
S10 = p("Two of the five phase 9 cures change nothing the user sees, and were switched on together with the "
        "others on 24 August 2026.", lead=True) + \
    table(["Cure", "What it does", "Measured effect"], [
        ["<b>Ghost eviction</b> (" + c("--sfratto-ms") + ", 15 000 ms)",
         "If a user's seat is held by a client silent for more than 15 s and a client of the <b>same user</b> "
         "asks for it, the seat goes to the newcomer. 15 s is half the 30 s silence clock: the browser's keep-alive "
         "is silent for up to 15 s, and a live idle client must not be evicted. Never between different users",
         "The ghost after a dropped wire went from 32.13 s and 14 refusals to 16.83 s and 7"],
        ["<b>Audio silence</b> (" + c("--niente-audio-silenzio") + " turns it off)",
         "A block whose samples are all exactly zero does not become a datagram",
         "102.1× less traffic on a still screen (557.6 → 5.5 kbit/s); 1 248 blocks silenced out of 1 248; "
         "+2 “missing” out of 5 000 at the client"],
    ], "«TAB» — The two invisible cures (bench 09-b84 and the ghost bench, 23–24 Aug 2026, test machine)") + \
    p("The eviction removes a false sentence rather than adding one: the old refusal claimed the user was "
      "“connected from another device” when it was usually their own dead session. The audio side is described "
      "in " + rif("Audio and clipboard") + ".")

# ── 11. The composition budget ────────────────────────────────────────────
S11 = p("Until 25 August 2026 the server accepted everyone and starved everyone together: on the saturated "
        "scene the eleventh user entered with " + c("negati 0") + " (refused: 0) and the first session fell from 39.60 to "
        "0.96 frames/s (−97.6 %). " + c("src/budget.c") + " is the cure: it computes, before a desktop is "
        "started, whether the machine can afford one more.", lead=True) + \
    table(["Where it gives way (Intel UHD 770, i5-13500T, 24 Aug 2026)", "Ceiling"], [
        ["The encoder alone (the two VDBOX engines)", "1.86 Gpixel/s in H.264 · 2.33 in HEVC"],
        ["<b>Composition</b> (the render engine " + c("rcs0") + ")", "<b>0.97 Gpixel/s — half</b>"],
    ], "«TAB» — Why the currency is the composed pixel, not the encoded one") + \
    p("The neck is upstream of REMOTIX: when the machine gives way, " + c("rcs0") + " is saturated by "
      + c("gnome-shell") + " at 99.5 % while " + c("remotix") + " sits at 0.00 %, and the video engine drops from "
      "48.7 % to 0.4 % because it has nothing left to encode. Switching off a single scene among eight sessions "
      "brought the rate back from 1.6 to 33.4 frames/s, reversibly. At the cliff the Mpixel/s coincide within "
      "0.6 % across canvas sizes while frames/s differ by 74.9 %: the budget can only <i>count</i> composition, "
      "and it counts it in composed pixels per second.") + \
    code("""
fits(inside, new)  <=>  sum of demand(inside) + peggiore(new)  <=  C * 1.01
                         AND  no tenant's median delay > 22.9 ms

demand(t)   = peggiore(t)                           if t never delivered, or has no delay sample
            = max(consegnato(t), F * peggiore(t))   otherwise
peggiore(t) = canvas_width * canvas_height * 39.54 / 1e6    Mpixel/s
""", "text", "The admission rule of budget.c (peggiore = worst case, consegnato = delivered)") + \
    table(["Constant", "Value", "Origin"], [
        [c("BUDGET_RITMO_MAX_FOT_S"), "39.54 frames/s", "What one session alone delivered on this hardware, first step of the climb to eleven sessions (1920×1080 H.264, saturated scene). The second number of the machine: re-measure it with the first"],
        [c("BUDGET_RITARDO_AFFANNO_MS"), "22.9 ms", "Geometric mean of healthy steps (≤ 13.1 ms) and broken steps (≥ 39.9 ms), which do not overlap. Valid for that scene and that hardware"],
        [c("BUDGET_RISERVA_PREDEFINITA"), "0.5", "With F = 0.5 the predictor makes 0 false yes and 0 false no on the data available"],
        [c("BUDGET_TOLLERANZA"), "1 %", "The repeatability of the meter (±0.6 %); the capacity is a peak that was seen to hold"],
        [c("SECCHI") + " × " + c("SECCHIO_US"), "8 × 250 ms = 2 s", "Window of delivered pixels; buckets let an idle tenant decay to zero"],
        [c("RITARDI") + " (delays)", "32 samples, median", "One hiccup must not refuse a user; ~0.8 s at 40 frames/s"],
    ], "«TAB» — The numbers of the budget") + \
    p("<b>The accumulator.</b> " + c("deposita_fotogramma()") + " (deposit a frame) in " + c("src/main.c") + " already received every "
      "frame of every child with width, height and capture instant, so no new channel between processes was "
      "needed: " + c("budget_deposita()") + " is called there, before the frame is broadcast and without any "
      "“is someone watching” guard. That is deliberate: a session whose client has left keeps encoding until its "
      "seat expires (a <i>ghost</i>), and costs the GPU as much as the others. The delay is capture → parent, an "
      "upper bound of the compositor's hold time, prudent in the right direction.") + \
    p("<b>The reserve.</b> Eight idle sessions admitted at 0.01 % each woke up within 19 ms and asked for "
      "8 × 14.4 = 115 % of the engine, plus the holder: 130 % of an engine that has 100. The worker lost 95.9 % of "
      "its rate and its delay went ×78 (9.7 → 756 ms). The phase 9 regulator cannot help — it drops frames already "
      "composed and encoded — so the reserve is the only defence: an idle tenant does not cost zero, it costs F "
      "times its worst case.") + \
    table(["Rule", "False no", "False yes", "Saturated ceiling", "Idle ceiling"], [
        [c("F = 0") + " (“delivered”)", "0", "0", "6", "unlimited — blind to wake-up"],
        ["<b>" + c("F = 0.5") + "</b>", "<b>0</b>", "<b>0</b>", "<b>6</b>", "<b>10</b>"],
        [c("F = 1") + " (“worst case”)", "1", "0", "5", "6"],
    ], "«TAB» — The reserve fraction, measured on the climb to eleven (phase 10 §6.9)") + \
    p("<b>Unknown is not zero.</b> A tenant that has not yet delivered a full 2-second window, or has no delay "
      "sample, is counted at its worst case; its canvas is that of its last frame or, if none, the stage canvas, "
      "the largest any session can get. The newcomer is counted at the minimum of the stage canvas and its "
      + c("video.misura_massima") + " (" + c("wt_misura_massima_di()") + ", the maximum size declared by that user's client), because the real canvas is only "
      "decided at " + c("SESSIONE") + ", later. A missing monotonic clock gives " + c("BUDGET_NON_SO") + " (“I don't know”), which "
      "admits and logs: a budget that refused for having failed to measure would make the user pay for our fault.") + \
    warn("the budget is off by default (" + c("--budget-mpixel-s 0") + ") and never calibrates itself. Before the "
         "machine has given way once, the highest capacity read is a lower bound, not a ceiling. Whoever types "
         + c("--budget-mpixel-s N") + " declares that N Mpixel/s of <i>composition</i> were measured at saturation on "
         "that machine. Passing the encoder's number instead would admit about 22 sessions where six fit.",
         "Off, and not self-tuning.") + \
    note("the delay gate never decided alone in the phase 10 runs (the pixel sum always did), and the compositor's "
         "buffer count, which would give the second half of the delay meter, lives in the child and does not cross "
         "the process boundary: only the measured delay is used.", "Not settled yet.")

# ── 12. Admission ─────────────────────────────────────────────────────────
AMMISSIONE = seq(
    [("Page", "browser", "light"), ("Transport", "webtransport.c", "blue"),
     ("Main loop", "consegna_verdetto()", "navy"), ("Budget", "budget.c", "amber"), ("Child", "figlio.c", "dark")],
    [(0, 1, "CIAO · CREDENZIALI"),
     ("nota", 2, "the PAM helper says yes"),
     (2, 2, "stages < --tetto-sessioni ?"),
     (2, 3, "open, add every stage, verdict"),
     (3, 2, "fits / does not fit / cannot tell", True),
     ("sep", "it fits (or the budget is off)"),
     (2, 4, "the child is born"),
     (2, 1, "verdict: admitted"),
     (1, 0, "AMMESSO · SESSIONE"),
     ("sep", "it does not fit"),
     (2, 1, "verdict, then close the user's sessions"),
     (1, 0, "CONGEDO 0x06 or 0x0E — no process started", True)],
    "«FIG» — Admission after PAM: the refusal is decided before any desktop process exists")

S12 = p("A refusal decided after the desktop has started is not a refusal: it is a login followed by an "
        "eviction. Measured in phase 10: a user who was never admitted had 42 processes and a "
        + c("gnome-shell") + ". Since 25 August 2026 both limits are checked in " + c("consegna_verdetto()")
        + " (deliver the verdict) <b>before</b> " + c("figli_assicura_da()") + " (ensure the user's child) starts "
        "the child.", lead=True) + AMMISSIONE + \
    table(["Check", "Counted on", "Refusal", "Phrase on the page (translated)"], [
        ["<b>Session cap</b> — " + c("--tetto-sessioni") + " (10)", c("palchi_quanti()")
         + " (how many stages): live children plus desktops found at startup and awaiting reattach",
         c("0x0E SESSIONE_NON_SERVIBILE") + " — an administrative limit",
         "the server could not open the session, it is not your fault; retry, and ask the administrator if it repeats"],
        ["<b>Composition budget</b> — " + c("--budget-mpixel-s"), "every stage with a child, plus the found desktops",
         c("0x06 BUDGET_PIENO") + " — a physical limit",
         "no more capacity for another desktop; the open sessions continue; a place frees as soon as someone leaves"],
    ], "«TAB» — The two limits and their two refusals") + \
    p("The two refusals are deliberately different (" + c("fasi/10-multi-tenant-e-il-budget.md") + " §8.1 D5): "
      "two different facts may not share an outcome. Neither is checked on a <b>resume</b> — a user whose stage "
      "already exists is already inside both counts, and refusing their reattach would be a false no on capacity "
      "they are spending anyway. The refusal is sent <i>after</i> " + c("trasporto_verdetto()") + " (hand the verdict to the transport), "
      "through " + c("wt_congeda_utente()") + " (dismiss every connection of the user): that order resets the failed-password counter of the address, and the "
      "client never sees " + c("AMMESSO") + ", only the farewell. The body of the " + c("CONGEDO") + " carries "
      "the figures (demand, declared capacity, the newcomer's worst case) for the log; the page shows its own "
      "phrase and does not print the body (RCP.md §7.1).") + \
    p("The page phrase for 0x06 promises only what is true at the gate. An earlier version suggested shrinking "
      "the window; at the gate the only canvas number is " + c("video.misura_massima") + ", the decoder's ceiling, "
      "so a smaller window got exactly the same refusal.") + \
    table(["Log line (area " + c("budget") + ")", "When"], [
        ["the three values in force, with the option names next to the numbers", "at startup, budget on or off"],
        ["budget ON at N Mpixel/s, reserve, delay threshold, worst case for the stage canvas, tolerance, slots", "at startup, if on"],
        ["budget OFF — this machine ADMITS EVERYONE", "at startup, if off"],
        ["verdict for «user»: ADMITTED/DENIED · " + c("negati") + " N (of which budget M) over K requests · values in force", "at every verdict, on or off"],
    ], "«TAB» — The budget's log lines, which every capacity bench reads") + \
    p(c("--tetto-sessioni N") + " sizes the four tables that count a user — the attached seats in "
      + c("src/rcp.c") + ", the children in " + c("src/figlio.c") + ", the presence table in " + c("src/main.c")
      + ", the stages in " + c("src/webtransport.c") + " — which used to be five hand-written copies (16, 16, 16, 16 "
      "and an 8). " + c("MAX_IN_VOLO") + " (maximum in flight) in " + c("src/aiutante.c") + " stays separate on purpose: it counts PAM "
      "verifications in flight, not sessions. The count of refusals, " + c("negati") + ", is written even with the "
      "budget off, because reading zero there is the fact that proves the product behaves as before.")

# ── 13. Capacity measured ─────────────────────────────────────────────────
S13 = p("How many sessions fit depends on the hardware and on the scene, and is not promised. The phase 10 "
        "numbers below were measured on one machine — Intel Core i5-13500T with the integrated Intel UHD 770 "
        "(" + c("renderD128") + "), 31 GB, 1920×1080 H.264, GNOME — on 24–25 August 2026.", lead=True) + \
    table(["Scene", "Sessions that fit", "Note"], [
        ["Saturated — the whole screen changes at every frame", "<b>6</b>", "The number the user judged: “considering that we are on a not particularly powerful integrated Intel card, 6 RDP sessions active at the same time does not seem a bad result to me” (DECISIONI.md §4.6-septies)"],
        ["Real desktop — windows, dragging, normal work", "<b>at least 11</b>", "The ceiling was not found: the bench ran out of users, not the machine"],
    ], "«TAB» — Phase 10 capacity on the Intel UHD 770") + \
    table(["Step", "Budget off", "Budget on (" + c("--budget-mpixel-s 480 --riserva 0.5") + ")"], [
        ["6", "472.5 Mpx/s · 37.98 frames/s · 0 I1 violations", "478.7 Mpx/s · 38.47 frames/s · 0 violations"],
        ["7", "396.0 Mpx/s · 27.28 frames/s · 6 violations", "refused with " + c("CONGEDO 0x06")],
        ["8", "35.3 Mpx/s · 2.12 frames/s", "does not exist"],
    ], "«TAB» — The budget on the saturated scene, 25 Aug 2026 (phase 10 §5.7)") + \
    p("At the sixth step the budget counted 496 Mpx/s while the machine delivered 478.7: the demand is an upper "
      "bound of what is delivered, and that margin is what makes the refusal fall on the seventh session, before "
      "the cliff, instead of the eighth, inside it. The control runs: budget off again → 26 violations and no "
      "0x06; ten <i>idle</i> sessions with the budget on → zero refused; budget set to 40 Mpx/s, below one 1080p "
      "session → the first user refused, zero processes started.") + \
    p("The phase 20 campaigns, on all four desktops and both cards, are in " + rif("Performance and capacity") + ".") + \
    tip("measure your own machine before switching the budget on: run the saturated scene with the budget off, "
        "find the step where the rate collapses, and pass the composed Mpixel/s of the last healthy step. "
        + c("BUDGET_RITMO_MAX_FOT_S") + " (39.54) is also a property of the test machine; on very different "
        "hardware it has to be re-measured and recompiled.", "Calibrating.")

# ── 14. Configuring ───────────────────────────────────────────────────────
S14 = p("On Debian, Ubuntu, Fedora and openSUSE the packaged unit reads " + c("/usr/share/remotix/remotix.conf")
        + " and then " + c("/etc/remotix/remotix.conf.d/*.conf") + "; any extra server option goes into the "
        + c("REMOTIX_OPZIONI") + " variable of a drop-in file there.", lead=True) + \
    code("""
# /etc/remotix/remotix.conf.d/capacity.conf
REMOTIX_OPZIONI=--budget-mpixel-s 480 --riserva 0.5 --tetto-sessioni 8
""", "bash", "Switching on the budget on a deb or rpm system") + \
    p("The Arch unit has no " + c("EnvironmentFile") + " and no " + c("REMOTIX_OPZIONI") + ": options are added "
      "by overriding " + c("ExecStart") + " with " + c("systemctl edit remotix") + ". After a restart, check the "
      "startup lines (" + rif("Logging and diagnostics") + "): each cure states whether it is on and with which "
      "number, and the budget prints its three values with the option names.") + \
    ul([
        "Not settled yet: the cap and the quality rise wait for the user's judgement on the real desktop.",
        "Not settled yet: a second, network budget next to the GPU one (ten sessions × the floor on the server's "
        "uplink) was named in phase 9 and never written.",
        "Not settled yet: the ban per address, shared by tenants behind one NAT, was deferred to a security "
        "chapter (" + c("DECISIONI.md") + " §4.6-octies).",
    ])

CHAPTER = ("Quality, degradation and budget", [
    ("The quality contract", S1),
    ("Where quality is decided", S2),
    ("Encoder rate control", S3),
    ("The 16 MiB frame cap and the quality ladder", S4),
    ("Quality recovery after the cap", S5),
    ("The video queue threshold", S6),
    ("The rate regulator", S7),
    ("Keyframe request pacing", S8),
    ("The dead line", S9),
    ("Ghost eviction and audio silence", S10),
    ("The composition budget", S11),
    ("Admission: the session cap and the budget", S12),
    ("Capacity measured in phase 10", S13),
    ("Configuring quality and capacity", S14),
])
