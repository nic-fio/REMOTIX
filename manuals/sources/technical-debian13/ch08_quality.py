from build import arrow, box, c, code, fig, h4, note, p, rif, seq, table, text, tip, ul, warn, zone

# ── 1 ───────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX does not chase a bitrate or a quality score. It follows a short contract written by the owner in " + c("SPECS.md") + " and in "
       + c("DECISIONS.md") + ": what may be spent when there is not enough, in which order, and what must never be spent. Every mechanism of "
       "this chapter exists to keep one line of that contract, and each one writes in the log, at startup, whether it is on and with which number.",
       lead=True) + \
    table(["Rule", "What it says", "Where it is enforced"], [
        ["<b>I1: the rate falls only on measure</b>", "The frame rate never drops out of prudence, to save bandwidth or because the scene is still. "
         "It drops only when a measurement proves the line does not carry, and the drop is written in the log next to the number that caused it.",
         "The rate regulator, the quality ladder, the decoder pace"],
        ["<b>Degrade in time, not in space</b>", "The image is never made coarse on purpose and the resolution never drops by the server's choice; "
         "frames are dropped instead. The canvas changes only when the client asks (" + c("FIT_CANVAS") + ").",
         "Constant QP by default; the ladder moves only on the 16 MiB cap; " + c("rcp_size_allowed()")],
        ["<b>A dead line is called dead</b>", "A line that no longer carries anything is not a slow line: the connection is closed and the user signs in again.", "The dead line"],
        ["<b>Full means refuse, with the reason</b>", "When the machine has no capacity left a newcomer is refused with " + c("BUDGET_FULL")
         + " before any desktop is started; those already working are never slowed down to make room.", "Admission"],
    ], "«TAB» — The rules that every quality mechanism serves") + \
    p("The numbers of " + c("SPECS.md") + " §3 (a minimum image of 480p, 25 frames/s, 24 bit; a desired image of 4K, 60 frames/s, 10 bit per channel; 50 ms for the "
      "server's own piece of the latency; a network floor of 30 Mbit/s) are <b>design goals, not measured promises</b>. What the code really uses are the "
      "constants named in this chapter. The shipped stream is H.264 or HEVC, 8 bit (" + rif("Video encoding") + "), and the capture asks for "
      + c("MOTION_FPS") + " = 60 frames/s. Bandwidth is a premise; the harder case the mechanisms react to is a line that loses, reorders and jitters, and "
      "most of them therefore watch queues and not Mbit/s.")

# ── 2 ───────────────────────────────────────────────────────────────────────
DOVE = fig(
    zone(20, 12, 200, 250, "Child process (per user)")
    + zone(240, 12, 200, 250, "Server main loop")
    + zone(460, 12, 200, 250, "Server: WebTransport")
    + zone(680, 12, 200, 250, "Browser page")
    + box(32, 44, 176, 50, "Capture", "60 frames/s requested", "blue")
    + box(32, 114, 176, 50, "Encoder", "QP 26 · 16 MiB ladder", "navy")
    + box(32, 184, 176, 50, "Quality rise · bit cap", "off by default", "grey")
    + box(252, 44, 176, 50, "deposit_frame()", "every frame of every child", "blue")
    + box(252, 114, 176, 50, "Budget accumulator", "budget_deposit()", "amber")
    + box(252, 184, 176, 50, "Admission", "cap · budget · verdict", "amber")
    + box(472, 44, 176, 50, "Rate regulator", "rate_brake()", "navy")
    + box(472, 114, 176, 50, "Queue threshold", "video_clear_out(), 100 ms", "navy")
    + box(472, 184, 176, 50, "Dead line", "stall 5 s · silence 10 s", "navy")
    + box(692, 44, 176, 50, "Stream reader", "FIN or RESET, open order", "blue")
    + box(692, 114, 176, 50, "Gap rule", "one key request per gap", "blue")
    + box(692, 184, 176, 50, "Decoder pace", "off unless --decoder-pace", "light")
    + arrow(120, 96, 120, 112) + arrow(210, 130, 250, 76)
    + arrow(340, 96, 340, 112) + arrow(340, 166, 340, 182)
    + arrow(430, 69, 470, 69) + arrow(560, 96, 560, 112)
    + arrow(650, 139, 690, 80) + arrow(780, 96, 780, 112)
    + arrow(780, 166, 780, 182),
    900, 270, "«FIG» — Where each quality and capacity mechanism lives; frames flow left to right")

S2 = p("Quality is not decided in one place. The encoder lives in the per-user child process; the budget and the admission live in the server's main loop "
       "(" + c("main.c") + "; in the default two-process server that is the network side, " + rif("Overall architecture") + "); the line-facing regulators live in "
       "the WebTransport layer; and the last word, what reaches the screen, is the page's. Each piece decides only on what it can measure locally.", lead=True) + DOVE + \
    table(["Mechanism", "Option (default)", "Process / file", "What it changes"], [
        "Line-facing cures (on by default)",
        ["Video queue threshold", c("--clear-threshold-ms N") + " (" + c("WT_CLEAR_THRESHOLD_MS") + " = 100; 0 = off)", "server · " + c("webtransport.c"),
         "A delta stuck in our queue is abandoned only if the queue cannot drain within N ms"],
        ["Rate regulator", c("--no-adaptive-rate") + " turns it off (on)", "server · " + c("webtransport.c"), "A frame is not sent while " + c("WT_RATE_SLOTS") + " = 2 deltas still have bytes in our queue"],
        ["Dead line", c("--no-dead-line") + " (on); " + c("--dead-line-stall-ms N") + " (5000); " + c("--dead-line-silence-s N") + " (10)", "server · " + c("webtransport.c"), "Closes the connection when the line no longer carries"],
        ["Ghost eviction", c("--eviction-ms N") + " (15000; 0 = off)", "server · " + c("rcp.c"), "A silent client of the same user loses its seat to a newcomer of that user"],
        ["Audio silence", c("--no-audio-silence") + " turns it off (on)", "child · " + c("audio.c"), "An all-zero audio block is not sent"],
        "Encoder cures (off by default)",
        ["Quality rise", c("--quality-recovery") + " (absent = off)", "child · " + c("encoder.c"), "After the 16 MiB ladder bit, climbs back one step at a time"],
        ["Bandwidth cap", c("--bandwidth-cap-mbit N") + " (0 = off)", "child · " + c("encoder.c"), "Switches the encoder from constant QP to QVBR (VBR on Vulkan) with a ceiling"],
        ["Decoder pace", c("--decoder-pace") + " (off)", "server and child · " + c("rcp.c") + ", " + c("child.c"), "A client whose decoder is behind may lower its own frame rate with " + c("PACE") + " (5 to 59/s)"],
        "Capacity",
        ["Composition budget", c("--budget-mpixel-s N") + " (0 = off)", "server · " + c("budget.c"), "Refuses a newcomer with 0x06 when the machine has no composition capacity left"],
        ["Reserve fraction", c("--reserve F") + " (" + c("BUDGET_DEFAULT_RESERVE") + " = 0.5)", "server · " + c("budget.c"), "How much of an idle tenant's worst case is kept aside"],
        ["Session cap", c("--session-cap N") + " (" + c("RCP_SESSION_CAP") + " = 10)", "server · " + c("rcp.c") + ", " + c("main.c"), "Administrative limit; refused with 0x0E. The declared limit of the product is 8 users"],
    ], "«TAB» — Every quality and capacity switch, its default and where it lives") + \
    p("Three of these live in the child, which is a separate program started with " + c("execve") + " and a freshly composed environment: they cannot travel as environment variables. "
      + c("children_phase9()") + " stores them and the child's command line carries " + c("--quality-recovery") + ", " + c("--bandwidth-cap-mbit") + " and "
      + c("--no-audio-silence") + " when it is built. Every switch writes its value in force at startup, <i>on and off</i>: «switched off» and «never had to act» must not look the same in the log. "
      "Extra server options go in " + c("REMOTIX_OPTIONS") + " of a drop-in under " + c("/etc/remotix/remotix.conf.d/") + " (" + c("debian/remotix.conf") + ", " + c("debian/remotix.service") + "); there is no other road to a value.") + \
    code("# /etc/remotix/remotix.conf.d/capacity.conf\nREMOTIX_OPTIONS=--budget-mpixel-s 480 --reserve 0.5 --session-cap 8",
         "bash", "Switching on the budget (the numbers are an example, not a recommendation)")

# ── 3 ───────────────────────────────────────────────────────────────────────
S3 = p("By default the encoder runs at a <b>constant QP of 26</b> (" + c("QP_HARDWARE") + " in " + c("child.c") + ", mode " + c("CODIFICATORE_QUALITA_QP") + "), with no bitrate, "
       "no buffer and no rate controller. With " + c("--bandwidth-cap-mbit N") + " it switches to a rate controller with a ceiling: <b>QVBR</b> on VA-API, <b>VBR</b> on Vulkan "
       "Video, which has no QVBR.", lead=True) + \
    p("Constant QP is the direct translation of I1 and of «never coarsen»: the quantiser is fixed, so the image of a quiet desktop never gets worse, and the bandwidth is "
      "simply what comes out. The comments of " + c("encoder.c") + " record measurements on the earlier test machine (2560×1080, Intel iHD, QP 26): the real desktop moving at full "
      "screen cost 0.204 Mbit/s and a film with grain at full screen cost 58.7 Mbit/s, which is why a cap that bit on ordinary content would be the wrong default and the cap is "
      "for the hard case only. Those numbers were not re-measured for this tree.") + \
    table(["Mode", "Verdict recorded in the comments of encoder.c"], [
        ["CQP, QP 26", "The default: no ceiling at all"],
        ["CBR", "Out: costs a fixed rate on a still screen for nothing"],
        ["VBR with a QP", "Out: the driver ignores the QP, so the quality ladder would become a no-op"],
        ["QVBR with a QP", "Chosen for the cap on VA-API: the ladder still acts and the ceiling holds"],
    ], "«TAB» — Rate-control modes, as the code and its comments settle them") + \
    p("The three numbers of the cap are <b>derived</b> from the floor given on the command line, never written by hand:") + \
    table(["Number", "Rule", "Function", "Why"], [
        ["Wire (maximum rate)", c("WIRE_CAP_QUOTA") + " = 80 % of the floor", c("wire_cap()"), "The rest is the audio, input, clipboard and QUIC overhead"],
        ["Working point (target rate)", c("POINT_CAP_QUOTA") + " = 75 % of the wire", c("point_cap()"), "<b>Never equal to the wire</b>: with the two equal the Intel driver silently deduces CBR (comment: lesson R31)"],
        ["Buffer (VBV)", c("VBV_CAP_MS") + " = 40 ms of the wire", c("reservoir_cap_bit()"), "The 40 ms target of the server's own piece of latency, not the 50 ms ceiling"],
    ], "«TAB» — The three numbers of the bandwidth cap") + \
    p("The mode is <b>asked for by name</b> (" + c("wanted_bitrate_mode()") + ") and checked against the mask the driver declares: on VA-API the declared rate-control bits are read with "
      + c("vaGetConfigAttributes") + " and printed in clear, and a mode the driver does not declare makes the encoder fail loudly instead of falling back to a mode nobody chose. "
      + c("cap_in_three_numbers()") + " refuses a working point not below the wire and a non-positive buffer, and " + c("reservoir_within_50_ms()") + " refuses a buffer longer than 50 ms. On Vulkan "
      "the cap becomes VBR with the requested QP as the floor of the controller (" + c("open_vulkan_card()") + "); without the cap the card must declare CQP (" + c("vulkan_fit()") + "). Every 10 s "
      "(" + c("BANDWIDTH_WINDOW_US") + ") the encoder also writes a «video bandwidth» line from the bytes it produced: the third witness that the ceiling is obeyed.") + \
    warn("the value passed is a <i>floor</i>, not a ceiling, and the comments of " + c("encoder.c") + " still describe the cap with 20 Mbit/s while " + c("main.c") + " and " + c("SPECS.md")
         + " name 30 Mbit/s. The three quota constants make the derivation independent of which one the operator passes.", "Which floor.") + \
    p("Not settled: the cap and the quality rise are off by default and have not been judged on a real desktop since this tree began; " + c("max_frame_size") + ", which QVBR would accept, is deliberately not used.")

# ── 4 ───────────────────────────────────────────────────────────────────────
S4 = p("RCP/1 forbids a video frame larger than 16 MiB: the sender must re-encode it at a lower quality and log it, never send it. That rule is the only thing that moves the QP "
       "of a running encoder.", lead=True) + \
    p("When a frame comes out of the card above " + c("FRAME_CAP") + " (16 × 1024 × 1024 bytes), " + c("compress_common()") + " logs it, records the rung on which the cap bit ("
      + c("failed_quality") + "), and " + c("lower_quality()") + " raises the QP by " + c("CRF_STEP") + " = 9, capped at 51. Changing quality closes and reopens the card context ("
      + c("change_quality()") + "), so the next frame is always a <b>keyframe</b>. The ladder from the default is 26, 35, 44, 51. A lossless request leaves at " + c("EMERGENCY_CRF") + " = 24.") + \
    table(["Frame", "How far down", "If it still does not fit"], [
        ["Keyframe", "The whole ladder: a keyframe may not be abandoned (RCP.md §5.2)", "At 51 it is not sent, and the log says «nothing left to lower»"],
        ["Delta", c("MAX_REENCODES") + " = 3 encodings in total: 26, 35, 44", "Abandoned. The reopened context makes the next frame a keyframe, so the client never loses its reference"],
    ], "«TAB» — How a frame over the cap is handled") + \
    p("The comments record why the step is 9: with a step of 6, a 7680×4320 keyframe of almost incompressible content measured 16.654 MiB at QP 38, over the cap, and 11.056 MiB at QP 44. "
      "The canvas has since been limited to 4096×2304 (" + c("RCP_CANVAS_MAX_W") + ", " + c("RCP_CANVAS_MAX_H") + "), and the ladder is a safety net for exceptional frames, not a working mechanism. "
      "At startup the encoder writes the ladder it will walk, with the values in force, by simulating " + c("lower_quality()") + " instead of printing a hand-written copy: two drafts of one rule would diverge "
      "on the day someone retunes the step. Every descent is declared in the log (area " + c("video") + ") with the frame size and its percentage of the cap.")

# ── 5 ───────────────────────────────────────────────────────────────────────
S5 = p("Without a way back the QP is a ratchet: one exceptional frame would leave the session at the bottom of the ladder for hours, with a quiet desktop permanently coarse. "
       + c("--quality-recovery") + " (" + c("encoder_quality_rises()") + ") adds the climb; it is off by default because it changes what the user sees.", lead=True) + \
    table(["Constant", "Value", "Meaning"], [
        [c("RISE_MARGIN"), "2 MiB (" + c("FRAME_CAP") + " / 8)", "A frame counts as calm only if it is comfortably under the cap"],
        [c("RISE_WAIT"), "120 frames (about 2 s at 60/s)", "Calm frames in a row before climbing one step"],
        ["Back onto the failed step", "twice the wait", "The rung where the cap bit is a fact, not a suspicion"],
        [c("RISE_WAIT_MAX"), "3840 frames (about 64 s)", "The wait doubles at every relapse and never comes back down"],
    ], "«TAB» — The numbers of the quality rise") + \
    p(c("raise_quality()") + " runs at the entry of the next frame, never with a packet in hand (closing the context frees its bytes). It climbs one step at a time and never above the "
      "quality the caller requested. A relapse right after a climb doubles the wait (" + c("recently_risen") + "). If the context does not reopen at the new value, it falls back to the old one: "
      "climbing is optional, and a cure that kills the session when it fails is worse than the defect.") + \
    p("Not settled: the three numbers are declared sufficient, not right.")

# ── 6 ───────────────────────────────────────────────────────────────────────
S6 = p("Each video frame travels on its own unidirectional QUIC stream (" + rif("Transport") + "). When a newer frame is produced while an older delta still has bytes in <i>our</i> send queue, "
       "RCP.md §5.1 allows (it does not require) a " + c("RESET_STREAM") + " of the old one. " + c("video_clear_out()") + " decides when to use that permission: an older delta is abandoned "
       "only if the video queue cannot drain within " + c("WT_CLEAR_THRESHOLD_MS") + " = 100 ms.", lead=True) + \
    code("""wait_ms = video_queue_bytes * smoothed_rtt / cwnd       (from ngtcp2; queue_drain_ms())
        = video_queue_bytes / WT_FLOOR_BYTE_MS          (fallback: no rtt or cwnd yet, 3750 bytes/ms = 30 Mbit/s)
wait <= threshold            -> keep every delta (counted, one log line per state change)
wait >  threshold            -> abandon the live deltas still in our queue
wait >  threshold, a KEY in queue -> keep the deltas behind it""", "text", "The decision of video_clear_out()") + \
    p("Only bytes still in our own queue are considered; what has already been handed to ngtcp2 is not taken back. The last rule exists because a large keyframe in the queue pushes the wait above "
      "the threshold by itself, abandoning the deltas behind it does not shorten it but opens a gap, which requests another large keyframe: abandons would climb by one per keyframe until the dead line "
      "fired (the keyframe spiral that RCP.md §5.2 names). Behind a keyframe the deltas are kept, and braking production is left to the rate regulator. " + c("--clear-threshold-ms 0") + " restores abandonment "
      "at every newer frame. The comments record a price of up to 160 ms of drift on a bad line and zero on a healthy one.")

# ── 7 ───────────────────────────────────────────────────────────────────────
S7 = p("The rate regulator is the mechanism that lowers the frame rate on a local fact: <b>" + c("backlog") + "</b>, the number of live, non-key deltas that still have bytes in our send queue, read when a new "
       "frame arrives and before " + c("video_clear_out()") + ".", lead=True) + \
    p(c("rate_brake()") + " returns «do not send» when " + c("backlog") + " reaches " + c("WT_RATE_SLOTS") + " = 2: one frame of overlap is allowed, two left behind are not. Nothing comes from outside, "
      "no loss rate, reordering or client silence can distort it, and there is no state to climb back: the quantity is re-read at every frame, so the episode ends by itself when the queue empties. "
      "Keyframes never pass through it; they have their own pacing.") + \
    table(["Fact", "Consequence"], [
        ["The threshold is its prerequisite", "With " + c("--clear-threshold-ms 0") + " the queue is emptied at every frame, " + c("backlog") + " can never exceed 1 and the regulator never fires; the startup log says so when that combination is chosen"],
        ["It brakes downstream of the encoder", "The dropped frame was already encoded and the encoder's references moved on, so a drop marks the stream as damaged (" + c("rcp_video_discarded_before_wire()") + ") and requests a keyframe at once ("
         + c("video_rule()") + ", the only place that asks the stage for a key). Without it the client would see an image decaying into tiles"],
        ["One keyframe per episode", c("needs_key") + " is cleared only when the key has left whole, and deltas behind that key are not abandoned"],
        ["Two log lines per episode", "«the rate DROPS» with " + c("backlog") + ", slots, queue bytes, " + c("cwnd") + ", bytes in flight and RTT; «the rate RISES» with the duration. Never one line per frame"],
        ["One line per second while on", c("rate_cycle()") + " prints how many times the backlog was read: zero reads means a still scene, not «zero backlog»"],
    ], "«TAB» — What the regulator depends on and what it costs") + \
    p("The congestion algorithm was never chosen: " + c("transport.c") + " keeps ngtcp2's default. On Wi-Fi a loss-based algorithm reads radio loss as congestion, which can manufacture the backlog "
      "this regulator measures (" + rif("Transport") + "). Not settled: " + c("WT_RATE_SLOTS") + " = 2 is declared, not calibrated, and the proper fix of the cost (stop <i>encoding</i> instead of dropping "
      "after encoding) would need the decision to reach the child.")

# ── 8 ───────────────────────────────────────────────────────────────────────
S8 = p("A keyframe is about ten times a delta. Asking for one at every sign of trouble is the spiral RCP.md §5.2 names, so both ends pace their requests.", lead=True) + \
    table(["Where", "Constant", "Value", "Rule"], [
        ["Page", "no constant name", "1 per gap, re-asked after 1000 ms", c("Viewer.hole()") + " in " + c("page.html") + ": while a gap is open no second request is sent; if the key has not arrived after 1 s it is asked again"],
        ["Server, RCP", c("V_GRACE_KEY"), "200 ms", "A request within 200 ms of the last keyframe sent may be ignored"],
        ["Server, towards the child", c("WT_KEY_REQUEST_MS"), "150 ms", "The floor between two requests to the capture process"],
        ["", c("WT_KEY_MARGIN_PC"), "120 %", "Margin on the time the last key needs to leave (key bytes × rtt / cwnd)"],
        ["", c("WT_KEY_CAP_MS"), "2000 ms", "The longest the image may stay broken: after that a key is asked anyway"],
        ["", c("WT_KEY_DEBT_CAP_MS"), "1000 ms", "A second safeguard: while the key debt is on, every refused frame can re-ask"],
    ], "«TAB» — The pacing of keyframe requests") + \
    p(c("key_interval_ms()") + " first looks at a fact: if the previous keyframe still has bytes in our queue, the answer is the 2-second ceiling. Otherwise it computes from ngtcp2's own cwnd and "
      "smoothed RTT how long a keyframe of the last size needs to leave, applies the margin, and never goes below 150 ms or above 2 s. Where there is bandwidth the cure declares itself inert; on a narrow line "
      "the image stays broken longer after a loss, which is the price, and in exchange the audio datagrams are not starved by keyframes asked faster than they can leave.")

# ── 9 ───────────────────────────────────────────────────────────────────────
S9 = p("This cure does not decide how well the desktop is seen but whether the connection still exists. The owner's decision is that a line losing in bursts is not a slow line but a broken one: the wire "
       "drops and the user signs in again. It is on by default and switched off with " + c("--no-dead-line") + ".", lead=True) + \
    table(["Cause", "Condition", "Default"], [
        ["<b>Stall</b>", "No byte of video has left for N ms <i>while there was something to send</i> (bytes of frames still queued, or a new frame from the child). A still scene never starts the count", c("WT_LM_STALL_MS") + " = 5000 ms"],
        ["<b>Silence</b>", "No packet from the client for N s, with at least " + c("WT_LM_MIN_PROVE") + " = 2 of our packets sent in the meantime", c("WT_LM_SILENCE_S") + " = 10 s"],
    ], "«TAB» — The two causes of the dead line") + \
    p(c("dead_line_judge()") + " evaluates both from monotonic local counters and ngtcp2's received-packet counter. When either fires, " + c("dead_line_fires()") + " writes one line starting with "
      + c("dead-line") + " that carries every number of the decision, and the transport, the only owner of the QUIC connection, closes it. The page then returns to the login form (" + rif("The browser page")
      + "). The comments record that the stall threshold sits 5.0 times above the longest empty second of a line that holds and 2.9 times below the freeze of a line that serves nobody (measured on emulated "
      "lines on the earlier test machine); a wrong value would throw out someone who is working, so whoever changes " + c("WT_LM_STALL_MS") + " must measure those two margins again.") + \
    warn("DECISIONS.md also lists «copious loss within 1–2 s» as a cause, and the code does not use it: the comments record that the loss fraction was refuted by its own bench, because on a reordering line "
         + c("pkt_lost") + " over " + c("pkt_sent") + " measures reordering, not loss. The fraction stays in the log line as " + c("permille=") + ", a witness rather than a judge.", "Loss is not a cause.")

# ── 10 ──────────────────────────────────────────────────────────────────────
S10 = p("Two of the line-facing cures change nothing the user sees, and are on by default.", lead=True) + \
    table(["Cure", "What it does", "Recorded effect"], [
        ["<b>Ghost eviction</b> (" + c("--eviction-ms") + ", " + c("DEFAULT_EVICTION") + " = " + c("SILENCE") + " / 2 = 15 000 ms)",
         "If a user's seat is held by a client silent for more than 15 s and a client of the <b>same user</b> asks for it, the seat goes to the newcomer. 15 s is half the " + c("SILENCE") + " clock (30 s): the browser's keep-alive is silent for up to 15 s and a live idle client must not be evicted. Never between different users",
         "The comments record the ghost after a dropped wire going from 32.13 s to 16.83 s"],
        ["<b>Audio silence</b> (" + c("--no-audio-silence") + " turns it off)", "A block whose samples are all exactly zero does not become a datagram",
         "The comments record 102.1 times less traffic on a still screen; the audio side is in " + rif("Audio and clipboard")],
    ], "«TAB» — The two invisible cures") + \
    p("The eviction removes a false sentence rather than adding one: the old refusal claimed the user was connected from another device when it was usually their own dead session.")

# ── 11 ──────────────────────────────────────────────────────────────────────
S11 = p("Without a budget the server accepts everyone and starves everyone together: the header of " + c("budget.h") + " records that on a saturated scene the eleventh user entered with zero refusals and the first "
        "session fell from 39.60 to 0.96 frames/s. " + c("budget.c") + " computes, before a desktop is started, whether the machine can afford one more. It is <b>off by default</b> and does not tune itself.", lead=True) + \
    p("<b>The currency is the composed pixel, not the encoded one.</b> The header records, for the Intel UHD 770 of the earlier test machine, that the encoder alone held 1.86 Gpixel/s in H.264 while "
      "composition (the render engine, saturated by gnome-shell) held 0.97: the neck is upstream of REMOTIX, and the budget can only <i>count</i> composition. The figures are from GNOME on that one machine.") + \
    code("""fits(inside, new)  <=>  sum of demand(inside) + worst(new)  <=  C * (1 + BUDGET_TOLERANCE)
                         AND  no tenant's median delay > BUDGET_STRAIN_DELAY_MS

demand(t)   = worst(t)                              if t never delivered, or has no delay sample
            = max(delivered(t), F * worst(t))       otherwise
worst(t)    = canvas_width * canvas_height * BUDGET_MAX_FPS / 1e6    Mpixel/s""", "text", "The admission rule of budget.c (budget_count_inside() and budget_count_verdict())") + \
    table(["Constant", "Value", "Meaning"], [
        [c("BUDGET_MAX_FPS"), "39.54 frames/s", "What one session alone delivered on the measuring hardware; the second number of the machine, to be re-measured together with " + c("--budget-mpixel-s")],
        [c("BUDGET_STRAIN_DELAY_MS"), "22.9 ms", "Geometric mean of the healthy steps (up to 13.1 ms) and the broken ones (from 39.9 ms), which did not overlap. Valid for that scene and hardware"],
        [c("BUDGET_DEFAULT_RESERVE"), "0.5", "At F = 0.5 the predictor made no false yes and no false no on the data available"],
        [c("BUDGET_TOLERANCE"), "0.01", "The repeatability of the meter; the capacity is a peak that was seen to hold, and a bare comparison would refuse that very state"],
        [c("BUCKETS") + " × " + c("BUCKET_US"), "8 × 250 ms = 2 s", "Window of delivered pixels; buckets let an idle tenant decay to zero"],
        [c("DELAYS"), "32 samples, median", "One hiccup must not refuse a user"],
    ], "«TAB» — The numbers of the budget") + \
    p("<b>The accumulator.</b> " + c("deposit_frame()") + " in " + c("main.c") + " already receives every frame of every child with width, height and capture instant, so no new channel is needed: "
      + c("budget_deposit()") + " is called there before the frame is broadcast, without an «is someone watching» guard. That is deliberate: a session whose client has left keeps encoding until its seat "
      "expires (a <i>ghost</i>) and costs the GPU as much as the others. The delay is capture to server, an upper bound of the compositor's hold time.") + \
    p("<b>The reserve.</b> An idle session does not cost zero: it costs " + c("F") + " times its worst case, because idle sessions wake up together. The header tabulates, for the climb it was calibrated on, "
      "F = 0 as blind to wake-up, F = 0.5 as the chosen value (cap 6 saturated, 10 idle), F = 1 with one false no. <b>Unknown is not zero:</b> a tenant that has not yet delivered a full 2-second window, or has no delay "
      "sample, is counted at its worst case. The newcomer is counted at the smaller of the stage canvas (" + c("CANVAS_W") + " × " + c("CANVAS_H") + " = 1920×1080 in " + c("main.c") + ") and its " + c("video.max_size")
      + " (" + c("wt_max_size_of()") + "), because the real canvas is decided later, at " + c("SESSION") + ". A missing monotonic clock gives " + c("BUDGET_UNKNOWN") + ", which admits and logs: a budget that refused for having "
      "failed to measure would make the user pay for the server's fault.") + \
    p("<b>A canvas that grows.</b> " + c("recanvas_fits_budget()") + " asks the same question again for a new " + c("FIT_CANVAS") + " that exceeds the stage canvas: the session's own stage is left out of the sum and the new "
      "size is judged as a newcomer's, and if it does not fit the client is answered " + c("NOT_NOW") + " and keeps the canvas it has (the " + c("canvas_fits") + " hook, " + c("wt_canvas_fits_hook()") + "). With the budget off it passes.") + \
    warn("the budget never calibrates itself. Before the machine has given way once, the highest capacity read is a lower bound, not a ceiling. Whoever types " + c("--budget-mpixel-s N") + " declares that N Mpixel/s of "
         "<i>composition</i> were measured at saturation on that machine. Passing the encoder's number instead would admit about 22 sessions where six fit on the measuring machine.", "Off, and not self-tuning.")

# ── 12 ──────────────────────────────────────────────────────────────────────
ADMISSION = seq(
    [("Page", "browser", "light"), ("Transport", "webtransport.c", "blue"),
     ("Main loop", "delivery_verdict()", "navy"), ("Budget", "budget.c", "amber"), ("Child", "child.c", "dark")],
    [(0, 1, "HELLO · CREDENTIALS"),
     ("note", 2, "the PAM helper says yes"),
     (2, 2, "stages < --session-cap ?"),
     (2, 3, "open, add every stage, verdict"),
     (3, 2, "fits / does not fit / cannot tell", True),
     ("sep", "it fits (or the budget is off)"),
     (2, 4, "the child is born"),
     (2, 1, "verdict: admitted"),
     (1, 0, "ADMITTED · SESSION"),
     ("sep", "it does not fit"),
     (2, 1, "verdict, then close the user's sessions"),
     (1, 0, "FAREWELL 0x06 or 0x0E: no process started", True)],
    "«FIG» — Admission after PAM: the refusal is decided before any desktop process exists")

S12 = p("A refusal decided after the desktop has started is not a refusal: it is a login followed by an eviction. Both limits are therefore checked in " + c("delivery_verdict()") + " <b>before</b> "
        + c("children_ensure_from()") + " starts the child.", lead=True) + ADMISSION + \
    table(["Check", "Counted on", "Refusal", "Meaning"], [
        ["<b>Session cap</b>: " + c("--session-cap") + " (10)", c("stage_count()") + ": live children plus desktops found again at startup and awaiting reattach",
         c("0x0E SESSION_UNSERVABLE") + ", an administrative limit", "The table is full, the machine is not"],
        ["<b>Composition budget</b>: " + c("--budget-mpixel-s"), "every stage with a child, plus the found desktops", c("0x06 BUDGET_FULL") + ", a physical limit",
         "No more capacity for another desktop; the open sessions continue; a place frees as soon as someone leaves"],
    ], "«TAB» — The two limits and their two refusals") + \
    p("The two refusals are deliberately different: two different facts may not share an outcome. A child that cannot be born for another reason (a name NSS does not resolve, uid 0, " + c("fork") + " failing) "
      "also ends in 0x0E, with the cause in the log. Neither limit is checked on a <b>resume</b>: a user whose stage already exists is already inside both counts, and refusing their reattach would be a false no. The "
      "refusal is sent after " + c("transport_verdict()") + ", through " + c("wt_dismiss_user()") + ": that order lets the admitted verdict reset the failed-password counter of that user on that address (" + c("login_resolve()") + " in " + c("rcp.c") + "; the counters of the address itself and of the /48 are not reset), and the client never sees " + c("ADMITTED") + ", only the "
      "farewell. The body of the " + c("FAREWELL") + " carries the figures for the log; the page shows its own phrase (" + rif("The RCP/1 protocol") + "). The phrase for 0x06 promises only what is true at the gate: at that "
      "point the only canvas number is " + c("video.max_size") + ", the decoder's ceiling, so shrinking the window would get the same refusal.") + \
    table(["Log line (area " + c("budget") + ")", "When"], [
        ["the three values in force, with the option names next to the numbers", "at startup, budget on or off"],
        ["budget ON at N Mpixel/s, reserve, delay threshold, worst case for the stage canvas, tolerance", "at startup, if on"],
        ["budget OFF: this machine ADMITS EVERYONE", "at startup, if off"],
        ["verdict for «user»: ADMITTED or DENIED, denied N (of which budget M) out of K requests", "at every verdict, on or off"],
    ], "«TAB» — The budget's log lines") + \
    p(c("--session-cap N") + " sizes the four tables that count a user (the attached seats in " + c("rcp.c") + ", the children in " + c("child.c") + ", the presence table in " + c("main.c") + ", the stages in "
      + c("webtransport.c") + "). " + c("MAX_IN_FLIGHT") + " in " + c("helper.c") + " stays separate on purpose: it counts PAM verifications in flight, not sessions. The count of refusals is written even with the budget off, "
      "because reading zero there is the fact that proves the product behaves as before.")

# ── 13 ──────────────────────────────────────────────────────────────────────
S13 = p("Four small headers, each with no dependency and no clock of its own (the caller passes the time), bound the work an unauthenticated or authenticated peer can ask of the single-threaded main loop, "
        "so that one noisy source cannot take frame rate away from everybody else. They are written so that a unit test can include each alone. The unit benches the comments name are not part of this repository.",
        lead=True) + \
    table(["Header", "What it bounds", "Numbers (constants of the header)"], [
        [c("hsrate.h"), "The <i>rate</i> of new handshakes: three token buckets taken together after the Retry token is verified and before the connection is accepted; a handshake needs a token from all three, and if any is empty nothing is charged",
         "Per address (IPv4 or IPv6 /64): " + c("HS_ADDR_RATE") + " 4/s, burst " + c("HS_ADDR_BURST") + " 16. Per IPv6 /48: " + c("HS_NET_RATE") + " 16/s, burst " + c("HS_NET_BURST") + " 32. Everybody: " + c("HS_ALL_RATE") + " 200/s, burst " + c("HS_ALL_BURST")
         + " 32. Tables of fixed size, least recently seen evicted: " + c("HS_ADDR_SLOTS") + " 256, " + c("HS_NET_SLOTS") + " 128"],
        [c("msgrate.h"), "A token bucket per client and per kind of message for what a logged-in client can send as fast as it likes: the five input types and " + c("REQUEST_KEY") + ", " + c("PACE") + ", " + c("VIEW") + ", " + c("LAYOUT") + ", " + c("FIT_CANVAS")
         + ". A message over the rate is consumed without effect and counted; " + c("FIT_CANVAS") + " is answered NOT_NOW instead. Not the clipboard (its own gate in " + c("rcp.c") + ")",
         c("msg_class_rate()") + " (per second, burst): pointer 2000/4000, button 1000/2000, wheel 1000/2000, letter 2000/4000, key position 2000/4000, request key 50/100, pace 100/200, view 100/200, layout 5/20, fit canvas 60/180. One summary line per " + c("MSG_WINDOW_MS") + " = 10 000 ms and at most " + c("MSG_LINES_PER_WINDOW") + " = 10 log lines of one kind per window"],
        [c("linebudget.h"), "A budget of log lines per time window, one counter for the process: the first lines of every window are written, the rest are counted, and when the window ends one line says how many were hidden. It protects journald from a flood provoked before any login",
         "Used with its own burst and window by " + c("transport.c") + " (" + c("SEND_FAIL_LINES") + ") and by " + c("webtransport.c") + " (" + c("WT_PRELOGIN_BURST") + " 20 lines per " + c("WT_PRELOGIN_WINDOW_MS") + " 10 000 ms per address, " + c("WT_PRELOGIN_GLOBAL_BURST") + " 100 in all)"],
        [c("dimcheck.h"), "The arithmetic on the sizes of a frame, in 64 bits: " + c("dim_stride_ok()") + " (a row of width×4 fits in the stride), " + c("dim_object_size()") + " (the 32-bit size of a DMA-BUF import), " + c("dim_frame_ok()") + " (consistent with what it declares and no larger than the canvas maximum)",
         "Used by " + c("capture.c") + ", " + c("encoder.c") + " and " + c("child.c") + " (against " + c("RCP_CANVAS_MAX_W") + " and " + c("RCP_CANVAS_MAX_H") + "); the sizes of a wlroots frame are the compositor's, so nothing else bounds them"],
    ], "«TAB» — Rate and size guards") + \
    p("<b>" + c("encbackoff.h") + "</b> belongs to the same family: " + c("enc_death_wait_ms()") + " returns the wait before an encoder is made again after it <i>died</i>, doubling from " + c("ENC_RETRY_MIN_MS") + " = 500 ms to "
      + c("ENC_RETRY_MAX_MS") + " = 10 s, and the count of deaths goes back to zero only after a frame was really sent (" + rif("Video encoding") + "). The handshake limits are part of " + rif("Login and its defences") + " as well.")

# ── 14 ──────────────────────────────────────────────────────────────────────
S14 = p("Two producers of unnecessary frames are cut before they reach the encoder, and one consumer-side limit is exposed to the client.", lead=True) + \
    ul(["<b>Empty damage.</b> When the compositor declares that nothing changed (" + c("SPA_META_VideoDamage") + " present and empty), " + c("damage_classify()") + " counts the frame in " + c("empty_damage") + " and the buffer goes back "
        "to PipeWire without being encoded (" + rif("Screen capture") + ").",
        "<b>The «unchanged» filter</b> (" + c("unchanged.h") + ", KDE only). A frame whose damaged rectangles hold the same bytes as the last frame that went out is not encoded. The filter measures its own cost: the mean cost of a "
        "look over a window (the first window of " + c("UC_COST_FIRST") + " = 30 looks, then every " + c("UC_COST_EVERY") + " = 300) switches it off if it exceeds " + c("UC_COST_HARD_US") + " = 10 000 µs whatever it holds back, or "
        + c("UC_COST_MAX_US") + " = 3000 µs when it held back fewer than one look in " + c("UC_YIELD_DIV") + " = 4; a switch-off for cost re-arms after " + c("UC_REARM_MS") + " = 5000 ms, and after " + c("UC_STRIKES_MAX")
        + " = 3 strikes it is off for the capture. A held-back frame goes out after " + c("UC_REFRESH_MS") + " = 250 ms at most. The full table of limits is in " + rif("Screen capture") + ".",
        "<b>Decoder pace.</b> With " + c("--decoder-pace") + " the server declares " + c("video.pace") + "; a client whose decoder queue stays behind may send " + c("PACE") + " (0x0012) with a ceiling clamped to "
        + c("RCP_PACE_FLOOR_FPS") + " = 5 to " + c("RCP_PACE_TOP_FPS") + " − 1 = 59 frames/s, and the child then takes fewer frames from the capture <i>before</i> encoding (" + c("pace_set()") + "), so no frame is thrown away and no keyframe "
        "is owed. A keyframe owed is never held back. It is off by default and RCP.md §13 marks it as proposed."]) + \
    h4("What the product adapts, and what it does not") + \
    table(["Quantity", "Who changes it", "How"], [
        ["Resolution (canvas)", "The client only", c("FIT_CANVAS") + ", bounded by " + c("rcp_size_allowed()") + " (320×240 to 4096×2304, even sides) and, above the stage canvas, by the budget. The server never lowers it to relieve a line"],
        ["Frame rate", "The line, by measurement", "Capture maximum " + c("MOTION_FPS") + " = 60; the rate regulator drops frames on backlog; the decoder pace (off) lowers it on the client's request; the unchanged filter and empty damage skip frames that carry no change"],
        ["Quality (QP)", "The 16 MiB cap, optionally the bandwidth cap", "Constant QP 26; the ladder 26, 35, 44, 51 only for an over-size frame; the climb back and the VBR/QVBR ceiling are off by default"],
        ["Admission", "The session cap and the budget", "0x0E and 0x06 before any process starts"],
    ], "«TAB» — Adaptation, by quantity") + \
    p("Capacity numbers for this tree, per card and desktop, are in " + rif("Performance and capacity") + ".") + \
    h4("What was verified, and what was not") + \
    ul(["<b>Verified (17 Nov 2026):</b> with the budget off (the default), " + c("prove/check-media.py") + " «two-sessions-budget» has two users animating at the same time and requires that neither goes below 25 frames/s and that the first does not lose more than 30 % of what it had alone; "
        "the multi-user checks of " + c("prove/all.sh") + " ran green on all four desktops; the dead line and the reconnection after a network drop are among the 34 checks per desktop of the 17 Nov round (" + c("PIANO.md") + ").",
        "<b>Not verified in this tree:</b> the budget switched on (the figures above are from the earlier test machine); the bandwidth cap and the quality rise on a real desktop; the decoder pace; a keyframe cap actually biting at 4096×2304; any of these on NVIDIA."])

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
    ("Rate and size guards: hsrate, msgrate, linebudget, dimcheck", S13),
    ("Frames that are not encoded, and what is adapted", S14),
])
