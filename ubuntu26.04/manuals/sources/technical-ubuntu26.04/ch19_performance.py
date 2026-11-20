"""Chapter 19 — Performance and capacity (Ubuntu 26.04). ONLY figures measured on Ubuntu 26.04 (the round vm-gnome-unione10 of 19 Nov 2026,
log folder prove/log/vm-gnome-unione10/ on the dev server: media.out, multiuser.out, lifecycle.out, resilience.out, ban.out, desktop.out,
summary.txt; the registry docs/REGISTRO-problemi.md, entry E4), the figures recorded in docs/DECISIONS.md (earlier build, quoted with their
date) and the constants of the code (src/budget.h, src/rcp.h, src/rcp.c, src/child.c, src/capture.c, src/mutter.c, src/page.html)."""
from build import c, h4, note, p, rif, sysf, table, tip, ul, warn

# ── 19.1 ─────────────────────────────────────────────────────────────────────
S1 = p("A number in this chapter is one of three kinds, and each is labelled. <b>Measured on Ubuntu 26.04</b>: printed by a check of "
       + c("prove/") + " in the round of 19 November 2026 (the log folder " + c("vm-gnome-unione10") + ", package " + c("unione10")
       + ", GNOME, one virtual machine). <b>Recorded</b>: written in " + c("docs/DECISIONS.md") + " or in the problem register from "
       "an earlier campaign or a hand test; it is quoted with its date and is NOT a measurement of this tree on a controlled bench. <b>Coded</b>: a "
       "constant or default in the source, cited by name; it is a limit or a target, not an observation.", lead=True) + \
    p("Nothing here was measured while writing the manual, and no figure is derived or extrapolated. The only desktop for which the full "
      "round of the checks was run on the release bench is GNOME (Ubuntu); Kubuntu, Xubuntu and Lubuntu were checked only by a short "
      "start-up check and by hand (" + rif("Appendix C — Known issues and open points") + "), so no timing in this chapter holds for them. "
      "A figure that was measured on Debian 13 and not repeated here is marked <b>measured on Debian 13 only</b> or left out. Where a figure that a "
      "reader would expect does not exist, the section says so (" + rif("Where no measurement exists") + ").") + \
    note("A measurement made by a check that drives a browser through its debugging interface includes the check's own cost. "
         "The tool's limits are given in " + rif("Testing") + ". The figures below are evidence that a property holds under the "
         "stated conditions, not a benchmark of the product.")

# ── 19.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The figures come from one virtual machine on the dev server and from the conditions of the check suite. The bench is the release bench of "
       "Ubuntu 26.04, not the container bench of Debian 13.", lead=True) + \
    ul([
        "<b>Machine.</b> A QEMU/KVM virtual machine with UEFI, installed from the Ubuntu 26.04 desktop image like a user would install it, with "
        + c("CPUS=8 MEM=12G DISKSZ=40G") + " (" + c("server/vm-radeon.sh") + "). The server's AMD Radeon is passed through to the machine by "
        + c("vfio-pci") + " (PCI address " + sysf("0000:03:00.0") + "); the machine sees that card and no other, and only one machine at a time can hold it. "
        "The model of the card is not printed by the logs of the round (" + c("docs/SPECS.md") + " §11.4 names an RX 6800 for the dev server; not verified for this "
        "machine). The time to power such a machine on or off is a property of the bench, not of the product, and is not reported.",
        "<b>Bench switches.</b> " + c("RX_BANCO=vm") + " selects the virtual-machine bench; " + c("RX_TEMPO=2") + " (the default of that bench) doubles every "
        "deadline of the checks. A figure that the product itself prints (for example \"client told after 0 s\") is not changed by it; a deadline "
        "that the check waits for is doubled. The checks reach the machine through the user-mode network of QEMU, so every client appears to the server as the "
        "address " + sysf("10.0.2.2") + " (" + rif("The VM bench") + ").",
        "<b>Client.</b> A real browser on the dev server driven by its debugging interface, in a headless compositor: Chrome " + c("156.0.8078.79")
        + " and Firefox " + c("153.7.0") + " as printed in the logs. The path to the machine is the virtual network of the host: nothing here says anything about bandwidth, "
        "loss or delay of a real link, except the single hand measurement of the problem register (" + rif("Where no measurement exists") + ").",
        "<b>Size.</b> The canvas of the media check was 1344x768 with Chrome (coded sizes 1344x770 and 1344x768 in the log) and 1392x800 with Firefox. No figure "
        "below holds for another size. The load average of the host at the time is printed by the check: 1.80 (picture and frame rate) and 1.26 (two sessions).",
        "<b>Codec.</b> Both browsers negotiated H.264 (" + c("avc1.640033") + ", 8 bit). The log says the server's H.264 encoder at start-up was "
        "<b>HARDWARE</b> on " + c("/dev/dri/renderD128") + " (the session's process had that node open). HEVC did not reach the pixel on the test browsers "
        "(the page's capability probe answered no to every HEVC string), as on Debian 13. The route (Vulkan Video or VA-API) is not printed in the lines read; "
        "the history of the work on Ubuntu records that in the virtual machines the video went through Vulkan on the Radeon and on a real machine "
        "through VA-API on the card of that machine (" + c("docs/STORIA-ubuntu-26.04.md") + ", 19 Nov 2026, hand test of the live image).",
    ])

# ── 19.3 ─────────────────────────────────────────────────────────────────────
S3 = p("From " + c("check-media.py") + " (" + c("screen-updates") + ", " + c("video") + ", " + c("codec") + ", " + c("two-sessions-budget")
       + "), GNOME on Ubuntu 26.04, in the round " + c("vm-gnome-unione10") + ". All four checks were PASS. The figures are those of Chrome; "
       "the log prints Firefox only for the codec check.", lead=True) + \
    table(["Measurement", "GNOME, Ubuntu 26.04 (Chrome)"], [
        ["counter at 8 Hz for 20 s: values seen / sent", "160 of 160 (450 screenshots, one per 43 ms)"],
        ["steps backwards in the counter", "0"],
        ["first sighting of a value, median (minimum)", "33 ms (5 ms)"],
        ["60 Hz bursts that stop: last value on screen after the last change, median / worst (9 stops)", "23 / 48 ms"],
        ["60 Hz animation: frames per second painted by the page (delivered)", "60.0 (60.1)"],
        ["flash to beep, sound after picture: sync error median (min to max)", "294 ms (276 to 346)"],
        ["sync drift first to last third of the 10 pairs", "-32 ms"],
        ["two sessions at 60 Hz: user 1 alone / together", "60.0 / 60.0 fps"],
        ["two sessions: user 2 together", "60.0 fps (delivered 60.0)"],
        ["sharpness at the default quality (stripes 1, 2, 4 px, horizontal 2 px, checker; coloured)", "1.00 each; 0.96"],
        ["black/white edge, 10 to 90% rise", "0 px"],
    ], "«TAB» — Picture and sound measured on Ubuntu 26.04 on 19 Nov 2026 (one session, 1344x768, virtual machine with the passed-through Radeon)") + \
    h4("How to read the table") + \
    ul([
        "<b>Timing figures carry the tool's uncertainty.</b> The browser is screenshotted: one screenshot takes about 50 ms, and the "
        "capture instant is somewhere inside it. The log itself gives the age of a picture as a range (median -12 ms if the capture "
        "is at the start of the screenshot, 40 ms if at its end, 13 ms taking the middle; 90th percentile 26 ms, maximum 39 ms). These are not glass-to-glass latency "
        "figures; the specification promises none, only 50 ms for the server's own piece.",
        "<b>Sound lags the picture by a constant 276 to 346 ms.</b> This is the audio cushion " + c("AUDIO_BUFFER_MS") + " = 250 in "
        + c("page.html") + ", a declared price (the comment in the page explains why 60 ms produced gaps). The check's own limits, in its code, are a "
        "median of at most 400 ms and a drift of at most 150 ms over the ten pairs; the log prints the lag as \"by design\" and leaves "
        "lip-sync judgement to the owner. The docstring of " + c("check-media.py") + " says 250 ms for the median; the code says 400 ms.",
        "<b>The two-session figure is a regression test, not a capacity test.</b> The budget knob is off in this run "
        "(" + c("--budget-mpixel-s 0.0 (OFF) --session-cap 10 --reserve 0.50") + " in the journal of the run); the rule being tested is that "
        "whoever is inside is not degraded (the first user lost 0 percent).",
        "<b>Debian 13 only.</b> The Debian 13 round of 17 Nov 2026 measured four desktops in containers (XFCE, LXQt and KDE at 58 to 62 frames per second painted, GNOME at "
        "39 frames per second). Those figures were taken on another machine, with another compositor version and another card, and are not repeated here: on "
        "Ubuntu 26.04 only the GNOME row above exists, and it shows 60.0. Neither log says why the two GNOME figures differ, and the "
        "difference must not be attributed to the distribution (the bench, the card and the compositor version all changed).",
    ]) + \
    h4("KDE: the lost frame, a property of the code") + \
    p("No picture figure was measured on Kubuntu with these checks. The code, however, has a mechanism that bears on the picture of KDE, described "
      "here only as a coded limit: " + c("capture_watch_sequence()") + " and " + c("capture_frame_lost()") + " in " + c("capture.c") + " watch the numbering of the "
      "buffers that KWin delivers; a gap forces a frame marked \"all changed\" and, after " + c("LOST_QUIET_MS") + " = 200 ms without an image, "
      "a poke through " + c("kwin_poke()") + ", at most " + c("LOST_POKES_MAX") + " = 10 times in a row, with a window of " + c("SEQ_WINDOW")
      + " = 600 buffer numbers (the mechanism is explained in " + rif("The lost frame (KWin)") + "). The comments of the code record measurements on a Kubuntu machine "
      "(a window left halfway through an animation for 18 to 26 s; 68 pokes on a still desktop, all answered by frames with empty damage that are not sent); they are comments, "
      "not a run of this manual.")

# ── 19.4 ─────────────────────────────────────────────────────────────────────
S4 = p("From " + c("check-lifecycle.py") + ", " + c("check-resilience.py") + ", " + c("check-ban.py") + " and " + c("check-multiuser.py")
       + " in the same round, GNOME only. They are measured, with the tools' resolution of one second.", lead=True) + \
    table(["Timing", "GNOME, Ubuntu 26.04", "Check"], [
        ["login refused (wrong password), three tries", "2.65, 2.65, 2.64 s", c("wrong-password")],
        ["login refused for a name that does not exist (median of three)", "2.65 s (wrong password of an existing user: 2.65 s)", c("same-answer")],
        ["Log Out: client told", "0 s", c("logout")],
        ["two and three users admitted together (each, to a working session)", "6 s", c("two-users") + ", " + c("three-users")],
        ["client told of inactivity (short-clock run, ceiling 30 s)", "29 s", c("clocks")],
        ["session closed after abandonment (short-clock run, ceiling 90 s)", "90 s", c("clocks")],
        ["server's own verdict after the UDP port was cut for 40 s", "11 s after the cut", c("network-drop")],
    ], "«TAB» — Session and login timings measured on Ubuntu 26.04 on 19 Nov 2026") + \
    ul([
        "The refusal time is the floor " + c("REJECT_FLOOR") + " = 2500 ms in " + c("rcp.c") + " plus the page's reaction; it is constant by design "
        "so that a wrong password and an unknown user are indistinguishable (the two medians above are equal).",
        "On Ubuntu the child may tell the clients \"the session is over\" before it dismantles its stage (" + c("session_over_early()") + " in " + c("child.c")
        + ", only on a certain death and never on KDE), so the \"client told\" time of a Log Out is not comparable with a Debian 13 figure. The "
        "Debian 13 figures (0 s on XFCE and LXQt, 5 s on GNOME, 4 s on KDE, round of 17 Nov 2026) were <b>measured on Debian 13 only</b> and are not carried over. "
        "A process of the child can wait up to 25 s for RealtimeKit where that service is installed and does not answer (a property of the container bench; entry B2 of the "
        "register), which is why the child tells the clients first.",
        "After a restart of the service the log of the round says that the client was told after 0 s, that the old desktop was gone and that the next login took one try "
        "(the desktops are closed with the service, DECISIONS-11 §11.56).",
        "The values of " + c("clocks") + " are from a run with the clocks shortened by a drop-in (30 s, 30 s, 90 s). At the defaults the "
        "service prints 30 s (fixed) for client silence, 1800 s for user inactivity and 3600 s for session abandonment; the defaults were "
        "not run to expiry.",
        "The \"login to a working session in 6 s\" of " + c("two-users") + " and " + c("three-users") + " is the harness's polling "
        "steps as much as the product's; it shows an upper bound, not a typical time.",
        "<b>Local login on KDE (hand test, not a check).</b> With the real login screen of a Kubuntu live image, the owner logged in locally while the remote "
        "desktop was open: the login was held in PAM, the client was sent away with 0x04 and the child closed the remote desktop in 10.9 s; on the GNOME live image the same "
        "step took 0.85 s (" + c("docs/STORIA-ubuntu-26.04.md") + ", 19 Nov 2026). The difference is the closing time of KDE described in the register (section D); it is a figure of one run on "
        "one machine, not a repeated measurement.",
    ])

# ── 19.5 ─────────────────────────────────────────────────────────────────────
S5 = p("The question \"how many users can one machine serve\" has no measured answer for this tree. What exists is (a) the recorded "
       "capacity campaign of August 2026, made on an earlier build and on Intel hardware, and (b) the most users any check attaches at once on Ubuntu.", lead=True) + \
    h4("Recorded: phase 10, 24 Aug 2026, on the earlier build") + \
    p("Source: " + c("docs/DECISIONS.md") + " §4.6-septies and §4.6-nonies. The campaign predates the 30 September 2026 change in which ffmpeg "
      "left the product and encoding moved to libva and Vulkan Video directly (comment of " + c("src/Makefile") + ", DECISIONS §10.25), so "
      "the numbers are those of another encoder path. The hardware was the Intel integrated card of the dev server; §4.6-septies calls it a "
      "UHD 730, a name that DECISIONS-11 §11.21 corrected to UHD 770. The campaign is independent of the distribution and of the package, and was not repeated on Ubuntu 26.04.") + \
    table(["Recorded figure", "Value", "Reading"], [
        ["sessions that fit on a fully changing screen (the worst scene)", "6", "the number the owner judged \"not a bad result\" on an integrated "
         "card (§4.6-septies)"],
        ["sessions on a real desktop (windows, dragging, normal work)", "at least 11", "the ceiling was NOT found: the users ran out, not the machine"],
        ["bare encoder ceiling, synthetic scene", "1.86 Gpixel/s H.264, 2.33 HEVC", "the two video engines of the card"],
        ["composition ceiling", "0.97 Gpixel/s (873 to 953 Mpixel/s in the other route)", "the compositor saturated first: gnome-shell at 99.5% while the product "
         "stood at 0%"],
        ["strain threshold of whoever is inside", "22.9 ms", "derived from healthy 13.1 ms or less and broken 39.9 ms or more, with no overlap; "
         "the constant " + c("BUDGET_STRAIN_DELAY_MS") + " in " + c("budget.h")],
    ], "«TAB» — Capacity figures recorded in DECISIONS.md (earlier build, not re-measured)") + \
    warn("These figures say where the limit comes from (the compositor's composition work, not the encoder), which is why the budget "
         "of " + rif("Quality, degradation and budget") + " counts composed pixels. They must not be quoted as the capacity of "
         "REMOTIX 1.0.0 for Ubuntu, and a figure without its hardware must not be quoted at all (DECISIONS §4.6-septies).") + \
    h4("Recorded: bandwidth and audio traffic, phase 9") + \
    ul([
        "DECISIONS §3.1-ter: the worst case on the real path (a client over a throttled link) asked for 21.5 to 23.1 Mbit/s and was held "
        "with all 7,125 frames delivered and painted, one keyframe, no abandonment.",
        "DECISIONS §3.1-septies: audio silence suppression cut the traffic of a still screen by 102 times (557.6 to 5.5 kbit/s).",
        "Both are on an earlier build and an earlier page; they are context, not a specification of 1.0.0.",
    ]) + \
    h4("Measured on Ubuntu 26.04: the most users tried at once") + \
    p("The widest multi-user check attaches three users together (" + c("three-users") + ", GNOME, PASS: each canvas its own "
      "colour, no input crossing); " + c("two-users") + " and " + c("same-user") + " also pass. " + c("check-media.py") + " runs two users animating at 60 Hz at once "
      "(60.0 frames per second each). " + c("check-desktop.py") + " " + c("session-cap") + " runs with the cap lowered to 2 and passes: the third user gets the farewell 0x0E "
      "and the two inside keep painting. Every other check runs with the default cap of " + c("RCP_SESSION_CAP") + " = 10 sessions in force, but none fills it. "
      "The same checks were not run on the virtual machines of Kubuntu, Xubuntu and Lubuntu.")

# ── 19.6 ─────────────────────────────────────────────────────────────────────
S6 = p("These are properties of the source, not observations. Each names its definition. The constants were read again in this tree.", lead=True) + \
    table(["Limit", "Value", "Where"], [
        ["<b>declared limit: users at the same time</b>", "<b>8</b> (owner's decision, " + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026)",
         "a declared value, not a constant: the technical default below is higher"],
        ["<b>declared limit: resolution</b>", "<b>up to 3K</b>; the size actually used depends on the client",
         "a declared value; the technical bounds below are higher"],
        ["sessions at once, default (technical)", "10 (configurable with " + c("--session-cap") + ")", c("RCP_SESSION_CAP") + " in " + c("rcp.h")],
        ["composition budget", "off by default (" + c("--budget-mpixel-s") + " 0); reserve 0.5 of the demand kept for whoever is inside",
         c("budget.h") + ", " + c("BUDGET_DEFAULT_RESERVE")],
        ["canvas size accepted (technical)", "320 to 4096 wide, 240 to 2304 high", c("rootside.c") + "; " + c("RCP_CANVAS_MAX_W") + " and " + c("RCP_CANVAS_MAX_H") + " in " + c("rcp.h")],
        ["frame rate of a stage", "60 frames per second at most", c("MOTION_FPS") + " in " + c("child.c")],
        ["minimum of the quality ladder (SPECS)", "480p, 25 fps, 24 bit (a guarantee, not a goal)", c("docs/SPECS.md") + " §3.1"],
        ["target of the specification", "4K, 60 fps, 10 bit per channel", c("docs/SPECS.md") + " §3.1 (a target; superseded as declared limit by §11.51/§11.58)"],
        ["frame ceiling on the video stream", "16 MiB; above it the frame is re-encoded smaller, not sent", c("V_CAP") + " in " + c("rcp.c") + ", " + c("FRAME_MAX") + " in " + c("child.c") + ", RCP §6.2"],
        ["audio cushion", "250 ms", c("AUDIO_BUFFER_MS") + " in " + c("page.html")],
        ["refusal floor for a wrong password", "2500 ms", c("REJECT_FLOOR") + " in " + c("rcp.c")],
        ["ban counters", "5 per user and address, 20 per address, 30 per IPv6 /48; windows 300, 300 and 600 s; bans of 15 min, 1 h, 12 h",
         c("LIMIT") + ", " + c("WINDOW_MS") + ", " + c("LADDER_MS") + " in " + c("rcp.c")],
        "Added or relevant on Ubuntu 26.04",
        ["lost-frame watch of KWin", c("LOST_QUIET_MS") + " 200 ms, " + c("LOST_POKES_MAX") + " 10, " + c("SEQ_WINDOW") + " 600", c("capture.c")],
        ["one call to Mutter in the scale correction", c("WAIT_CALL_MS") + " = 15 000 ms per call; the child tries to bring the monitor scale back to 1 once, with three calls at most, "
         "so about 45 s in the worst case before it gives up and refuses the stage with 0x0E (comment in " + c("mutter.h") + ")",
         c("mutter_scale_to_one()") + " in " + c("mutter.c")],
        ["wait of a young child for RealtimeKit", "up to 25 s where the service is installed and does not answer (a bench property: register, B2)", c("child.c") + " (comments of the " + c("MSG_SESSION_FINISHED") + " and " + c("MSG_LOCAL_FOUND") + " handlers)"],
        ["a child told to close counts as closing", c("CLOSING_GRACE_MS") + " = 30 000 ms", c("child.c")],
    ], "«TAB» — Limits fixed in the code") + \
    p("The decision of 17 Nov 2026, recorded in the plan of the Debian tree, that the address ban stays at 20 failed attempts in 5 minutes matches the second row of the ban "
      "counters. The constants of the first twelve rows are the same as on Debian 13 (the diff of " + c("rcp.h") + " and " + c("budget.h") + " does not touch them, "
      "and the lines of " + c("rcp.c") + " that define them are unchanged); the last four rows are specific to this tree.")

# ── 19.7 ─────────────────────────────────────────────────────────────────────
S7 = p("This list is deliberate: a manual that stays silent about a missing measurement invites a reader to invent one.", lead=True) + \
    table(["Not measured", "What is known instead"], [
        ["capacity per number of users on 1.0.0", "the recorded campaign on the earlier build (above); three users attached together and two at 60 Hz tested "
         "on Ubuntu GNOME. No run that fills the default cap of 10 and no search for the point where service degrades"],
        ["timings and frame rate on Kubuntu, Xubuntu and Lubuntu", "none: the full round was run on GNOME only. For the other three the release was checked by a short "
         "start-up check with the Radeon and by the owner's hand tests"],
        ["after the bench started to enter the machine as root", "only the ban check and the Firefox audio check were run again (all PASS); the full round was not repeated"],
        ["a card by vendor and model", "the log shows " + c("/dev/dri/renderD128") + " and not the card; no per-card table exists. The only card on the Ubuntu release bench is the "
         "passed-through Radeon"],
        ["NVIDIA, and the integrated Intel card with GNOME 50", "no run recorded on Ubuntu 26.04; the functional suite was never run on an Intel card with this GNOME"],
        ["4096x2304 and larger canvases", "the declared limit is 3K; the coded limit is 4096x2304. In the round, " + c("canvas-limits") + " is PASS on GNOME: for a view of "
         "3840x2160 the canvas is 3824x2160, and for views of 4096x2304 and 5120x2880 it stays at 3840x2160, the last rung of the page's own size ladder "
         "(" + c("MEASURE_PROBES") + " in " + c("page.html") + "). No frame rate or quality figure at those sizes exists"],
        ["bitrate of the current build", "none printed by the round on Ubuntu. The only bitrate figures in the files read are the phase 9 ones above and the hand measurement below"],
        ["real networks", "all figures of the round are on a virtual network; no loss, delay, jitter or throughput measurement of 1.0.0 over a real link is recorded, "
         "except the single case below"],
        ["CPU and memory per session", "no per-session CPU or memory figure was found in the plan file, the register, the docs read or the logs read"],
        ["duration of a whole run of all.sh", "the full GNOME round took 47 minutes on the virtual-machine bench with " + c("RX_TEMPO=2") + " (" + c("docs/STORIA-ubuntu-26.04.md") + "); the sum of "
         "the time limits of the fifteen steps is 17 860 s, multiplied by " + c("RX_TEMPO") + " on that bench (" + rif("Testing") + ")"],
    ], "«TAB» — Where no measurement exists") + \
    h4("A real phone as client: small stutters in the video (register E4)") + \
    p("The owner reported small stutters when playing a video (1440p and Full HD) in the remote GNOME session from Chrome on an Android phone, on the virtual machine of "
      "Ubuntu on 19 Nov 2026; from the tablet (Chrome on Linux) he did not notice them. The server was measured during 40 s of video towards the phone "
      "(" + c("docs/REGISTRO-problemi.md") + ", entry E4; the raw logs of this measurement were not found on the dev server, and the figures are quoted from the register):") + \
    table(["Figure", "Value"], [
        ["packets lost", "none"],
        ["bit rate", "1.5 to 5 Mbit/s"],
        ["seconds of video at 60 frames per second", "35 of 39 (the others: 57, 56, 52 and 43 frames in the second)"],
        ["frames sent late", "about one in twenty, by a few milliseconds"],
        ["network delay to the phone", "8 ms typical, peaks up to 125 ms (tablet: 3.5 ms, peaks 27 ms)"],
    ], "«TAB» — The one measurement towards a real phone (19 Nov 2026, recorded in the register)") + \
    p("The cause was not isolated: the phone (Wi-Fi and the Android decoder), the video player inside the virtual machine, the frame cadence of a virtual machine and the encoding path on the "
      "Radeon are all still possible. It is an open, non-blocking case (" + rif("Ubuntu: open points") + "), not a benchmark.") + \
    tip("A measurement worth adding first, if capacity matters: " + c("check-multiuser.py") + " style runs at 4, 6, 8 and 10 users with the "
        "budget off, on one named card, recording the composition delay of " + c("BUDGET_STRAIN_DELAY_MS") + ". To settle the Android case: the same video "
        "towards the tablet with the same measurement on the server, and the same test on a real machine. These are suggestions, not plans "
        "recorded anywhere.", "Suggestion.")

CHAPTER = ("Performance and capacity", [
    ("How to read the numbers of this chapter", S1),
    ("The test machine and the conditions of the measurements", S2),
    ("Picture, frame rate and sound measured on 19 November 2026", S3),
    ("Session and login timings measured on 19 November 2026", S4),
    ("Capacity: the recorded measurements and what they do not cover", S5),
    ("Limits fixed in the code", S6),
    ("Where no measurement exists", S7),
])
