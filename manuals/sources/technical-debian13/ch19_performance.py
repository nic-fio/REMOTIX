"""Chapter 19 — Performance and capacity. ONLY measured numbers (the logs v160-<de>/media.out, lifecycle.out,
resilience.out, ban.out, multiuser.out on the dev server; PIANO.md; docs/DECISIONS.md §4.6-septies and §4.6-nonies, §3.1-ter,
§3.1-septies) and constants of the code (src/budget.h, src/rcp.h, src/rcp.c, src/child.c, src/rootside.c, src/page.html)."""
from build import c, h4, note, p, rif, sysf, table, tip, ul, warn

# ── 19.1 ─────────────────────────────────────────────────────────────────────
S1 = p("A number in this chapter is one of three kinds, and each is labelled. <b>Measured now</b>: printed by a check of "
       + c("prove/") + " in the round of 17 November 2026 on the code that became 1.0.0. <b>Recorded</b>: written in "
       + c("docs/DECISIONS.md") + " from an earlier campaign on an earlier build; it is quoted with its date and is NOT a measurement "
       "of this tree. <b>Coded</b>: a constant or default in the source, cited by name; it is a limit or a target, not an "
       "observation.", lead=True) + \
    p("Nothing here was measured while writing the manual, and no figure is derived or extrapolated. Where a figure that a reader "
      "would expect does not exist, the section says so (" + rif("Where no measurement exists") + ").") + \
    note("A measurement made by a check that drives a browser through its debugging interface includes the check's own cost. "
         "The tool's limits are given in " + rif("Testing") + ". The figures below are evidence that a property holds under the "
         "stated conditions, not a benchmark of the product.")

# ── 19.2 ─────────────────────────────────────────────────────────────────────
S2 = p("All figures of the round of 17 November come from one machine, the dev server, and from the conditions of the test suite.",
       lead=True) + \
    ul([
        "<b>Machine.</b> A single server with an integrated Intel card (the UHD 770, per " + c("docs/DECISIONS-11.md") + " §11.21) and an "
        "AMD Radeon RX 6800 (" + c("docs/SPECS.md") + " §11.4, measured 1 Oct 2026). The logs name the encoder node as "
        + c("/dev/dri/renderD128") + " and do not say which of the two cards that is.",
        "<b>Boxes.</b> Four systemd containers on the host network (" + rif("The four test boxes") + "). The four desktops ran at the same "
        "time on the one machine; the " + c("media") + " check reports the host load average at the moment: 3.89 and 5.32 (XFCE), 4.05 and "
        "4.13 (LXQt), 4.63 and 5.12 (GNOME), 5.14 and 6.21 (KDE), for its two measuring phases.",
        "<b>Client.</b> A real browser on the same machine, on 127.0.0.1, with a headless software-rendering compositor (Chrome "
        + c("156.0.8078.79") + ", Firefox " + c("153.7.0") + " as printed in the logs). There is no network between the server and the "
        "browser, so nothing here says anything about bandwidth, loss or delay of a real link.",
        "<b>Size.</b> The canvas of the media check was 1344x768 with Chrome (the log prints the coded sizes 1344x770 and 1344x768) and 1392x800 with Firefox. No figure "
        "below holds for another size.",
        "<b>Codec.</b> Both browsers negotiated H.264 (" + c("avc1.640033") + ", 8 bit), encoded in hardware. HEVC "
        "does not reach the pixel on the test browsers (the page's capability probe answered no to every HEVC string).",
    ])

# ── 19.3 ─────────────────────────────────────────────────────────────────────
S3 = p("From " + c("check-media.py") + " (" + c("screen-updates") + ", " + c("video") + ", " + c("codec") + ", " + c("two-sessions-budget")
       + "), Chrome, in the final round. Every one of these four checks was PASS on all four desktops.", lead=True) + \
    table(["Measurement", "XFCE", "LXQt", "GNOME", "KDE Plasma"], [
        ["counter at 8 Hz for 20 s: values seen / sent", "159 of 159", "159 of 159", "160 of 160", "160 of 160"],
        ["steps backwards in the counter", "0", "0", "0", "0"],
        ["first sighting of a value, median", "20 ms", "20 ms", "13 ms", "18 ms"],
        ["60 Hz bursts that stop: last value on screen after the last change, median / worst", "16 / 34 ms", "30 / 52 ms", "31 / 44 ms", "24 / 44 ms"],
        ["60 Hz animation: frames per second painted by the page", "61.7", "61.8", "39.3", "57.8"],
        ["flash to beep, sound after picture: sync error median (min to max)", "294 ms (273 to 350)", "305 ms (279 to 355)",
         "287 ms (267 to 327)", "267 ms (245 to 301)"],
        ["sync drift first to last third of the 10 pairs", "-31 ms", "-14 ms", "+8 ms", "-7 ms"],
        ["two sessions at 60 Hz: user 1 alone / together", "61.8 / 61.7 fps", "61.7 / 61.7 fps", "38.6 / 39.9 fps", "58.0 / 57.9 fps"],
        ["two sessions: user 2 together", "61.7 fps", "61.7 fps", "40.1 fps", "57.8 fps"],
        ["sharpness at the default quality (stripes 1, 2, 4 px, checker)", "1.00 each", "1.00 each", "1.00 each", "1.00, 1.00, 0.99, 1.00"],
        ["black/white edge, 10 to 90% rise", "0 px", "0 px", "0 px", "0 px"],
    ], "«TAB» — Picture and sound measured on 17 Nov 2026 (one session, 1344x768, loopback)") + \
    h4("How to read the table") + \
    ul([
        "<b>Timing figures carry the tool's uncertainty.</b> The browser is screenshotted: one screenshot takes about 49 ms, and the "
        "capture instant is somewhere inside it. The log itself gives the age of a picture as a range (median -14 ms if the capture is "
        "at the start of the screenshot, 36 ms if at its end, 11 ms taking the middle, XFCE). These are not glass-to-glass latency "
        "figures; the specification promises none, only 50 ms for the server's own piece.",
        "<b>Sound lags the picture by a constant 245 to 355 ms.</b> This is the audio cushion " + c("AUDIO_BUFFER_MS") + " = 250 in "
        + c("page.html") + ", a declared price (the comment in the page explains why 60 ms produced gaps). The check's own limits, in its code, are a "
        "median of at most 400 ms (the 250 ms cushion plus 150 ms) and a drift of at most 150 ms over the ten pairs; the logs print the lag as "
        "\"by design\" and leave lip-sync judgement to the owner. The docstring of " + c("check-media.py") + " says 250 ms for the median; "
        "the code says 400 ms.",
        "<b>The 60 Hz animation figure is the frame rate the page painted.</b> XFCE, LXQt and KDE reach 58 to 62; GNOME 39, alone as "
        "with a second session. The logs do not establish why GNOME is lower, and nothing in the files read for this chapter does.",
        "<b>The two-session figure is a regression test, not a capacity test.</b> The budget knob is off in these runs "
        "(" + c("--budget-mpixel-s 0.0 (OFF) --session-cap 10 --reserve 0.50") + " in the journal of the run); the rule being tested is that "
        "whoever is inside is not degraded (the first user lost 0, 0, -3 (a gain) and 0 percent).",
    ])

# ── 19.4 ─────────────────────────────────────────────────────────────────────
S4 = p("From " + c("check-lifecycle.py") + ", " + c("check-resilience.py") + ", " + c("check-ban.py") + " and " + c("check-multiuser.py")
       + " in the same round. They are measured, with the tools' resolution of one second.", lead=True) + \
    table(["Timing", "XFCE", "LXQt", "GNOME", "KDE Plasma", "Check"], [
        ["login refused (wrong password), three tries", "2.64, 2.53, 2.64 s", "2.63, 2.63, 2.64 s", "2.64, 2.64, 2.64 s",
         "2.65, 2.65, 2.65 s", c("wrong-password")],
        ["Log Out: client told", "0 s", "0 s", "5 s", "4 s", c("logout")],
        ["three users admitted together (each, to a working session)", "6 s", "6 s", "6 s", "6 s", c("three-users")],
        ["client told of inactivity (short-clock run, ceiling 30 s)", "29 s", "29 s", "29 s", "29 s", c("clocks")],
        ["session closed after abandonment (short-clock run, ceiling 90 s)", "89 s", "92 s", "92 s", "92 s", c("clocks")],
    ], "«TAB» — Session and login timings measured on 17 Nov 2026") + \
    ul([
        "The row of the table that timed a login after a restart of the service, “with the session found”, was removed: it belonged to "
        "the check as it was before 18 Nov 2026, which expected the same desktop back. Since the desktops are closed with the service "
        "(§11.56) the check was re-aligned (" + rif("Testing") + ") and no timing of it is recorded here.",
        "The refusal time is the floor " + c("REJECT_FLOOR") + " = 2500 ms in " + c("rcp.c") + " plus the page's reaction; it is constant by design "
        "so that a wrong password and an unknown user are indistinguishable.",
        c("network-drop") + " (XFCE log): the UDP port was cut for 40 s; the server's own verdict (the dead-line close) came 10 s after the cut, "
        "and a login right after the cut got the session back in one try. The check docstring says the specification writes 30 s for this "
        "clock and the code 10 s.",
        "The values of " + c("clocks") + " are from a run with the clocks shortened by a drop-in (30 s, 30 s, 90 s). At the defaults the "
        "service prints 30 s (fixed) for client silence, 1800 s for user inactivity and 3600 s for session abandonment; the defaults were "
        "not run to expiry.",
        "The \"login to a working session in 6 s\" of " + c("three-users") + " is the harness's polling "
        "steps as much as the product's; it shows an upper bound, not a typical time.",
    ])

# ── 19.5 ─────────────────────────────────────────────────────────────────────
S5 = p("The question \"how many users can one machine serve\" has no measured answer for this tree. What exists is (a) the recorded "
       "capacity campaign of August 2026, made on an earlier build, and (b) the most users any check attaches at once.", lead=True) + \
    h4("Recorded: phase 10, 24 Aug 2026, on the earlier build") + \
    p("Source: " + c("docs/DECISIONS.md") + " §4.6-septies and §4.6-nonies. The campaign predates the 30 September 2026 change in which ffmpeg "
      "left the product and encoding moved to libva and Vulkan Video directly (comment of " + c("src/Makefile") + ", DECISIONS §10.25), so "
      "the numbers are those of another encoder path. The hardware was the Intel integrated card of the dev server; §4.6-septies calls it a "
      "UHD 730, a name that DECISIONS-11 §11.21 corrected to UHD 770.") + \
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
         "REMOTIX 1.0.0, and a figure without its hardware must not be quoted at all (DECISIONS §4.6-septies).") + \
    h4("Recorded: bandwidth and audio traffic, phase 9") + \
    ul([
        "DECISIONS §3.1-ter: the worst case on the real path (a client over a throttled link) asked for 21.5 to 23.1 Mbit/s and was held "
        "with all 7,125 frames delivered and painted, one keyframe, no abandonment.",
        "DECISIONS §3.1-septies: audio silence suppression cut the traffic of a still screen by 102 times (557.6 to 5.5 kbit/s).",
        "Both are on an earlier build and an earlier page; they are context, not a specification of 1.0.0.",
    ]) + \
    h4("Measured now: the most users tried at once") + \
    p("The widest multi-user check attaches three users together (" + c("three-users") + ", XFCE, LXQt, GNOME and KDE: all PASS, each canvas its own "
      "colour, no input crossing). " + c("check-media.py") + " runs two users animating at 60 Hz at once. " + c("check-desktop.py") + " "
      + c("session-cap") + " runs with the cap lowered to 2. Every other check runs with the default cap of " + c("RCP_SESSION_CAP") + " = 10 sessions in force, but none fills it.")

# ── 19.6 ─────────────────────────────────────────────────────────────────────
S6 = p("These are properties of the source, not observations. Each names its definition.", lead=True) + \
    table(["Limit", "Value", "Where"], [
        ["<b>declared limit: users at the same time</b>", "<b>8</b> (owner's decision, " + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026)",
         "a declared value, not a constant: the technical default below is higher"],
        ["<b>declared limit: resolution</b>", "<b>up to 3K</b>; the size actually used depends on the client",
         "a declared value; the technical bounds below are higher"],
        ["sessions at once, default (technical)", "10 (configurable with " + c("--session-cap") + ")", c("RCP_SESSION_CAP") + " in " + c("rcp.h")],
        ["composition budget", "off by default (" + c("--budget-mpixel-s") + " 0); reserve 0.5 of the demand kept for whoever is inside",
         c("budget.h") + ", " + c("BUDGET_DEFAULT_RESERVE")],
        ["canvas size accepted (technical)", "320 to 4096 wide, 240 to 2304 high, multiples of 16 per side as the checks judge it", c("rootside.c") + "; " + c("RCP_CANVAS_MAX_W") + " and " + c("RCP_CANVAS_MAX_H") + " in " + c("rcp.h")],
        ["frame rate of a stage", "60 frames per second at most", c("MOTION_FPS") + " in " + c("child.c")],
        ["minimum of the quality ladder (SPECS)", "480p, 25 fps, 24 bit (a guarantee, not a goal)", c("docs/SPECS.md") + " §3.1"],
        ["target of the specification", "4K, 60 fps, 10 bit per channel", c("docs/SPECS.md") + " §3.1 (a target; superseded as declared limit by §11.51/§11.58)"],
        ["frame ceiling on the video stream", "16 MiB; above it the frame is re-encoded smaller, not sent", c("V_CAP") + " in " + c("rcp.c") + ", " + c("FRAME_MAX") + " in " + c("child.c") + ", RCP §6.2"],
        ["audio cushion", "250 ms", c("AUDIO_BUFFER_MS") + " in " + c("page.html")],
        ["refusal floor for a wrong password", "2500 ms", c("REJECT_FLOOR") + " in " + c("rcp.c")],
        ["ban counters", "5 per user and address, 20 per address, 30 per IPv6 /48; windows 300, 300 and 600 s; bans of 15 min, 1 h, 12 h",
         c("LIMIT") + ", " + c("WINDOW_MS") + ", " + c("LADDER_MS") + " in " + c("rcp.c")],
    ], "«TAB» — Limits fixed in the code") + \
    p("The PIANO.md decision of 17 Nov 2026 that the address ban stays at 20 failed attempts in 5 minutes matches the second row of the ban "
      "counters.")

# ── 19.7 ─────────────────────────────────────────────────────────────────────
S7 = p("This list is deliberate: a manual that stays silent about a missing measurement invites a reader to invent one.", lead=True) + \
    table(["Not measured", "What is known instead"], [
        ["capacity per number of users on 1.0.0", "the recorded campaign on the earlier build (above); three users attached together and two at 60 Hz tested "
         "now. No run that fills the default cap of 10 and no search for the point where service degrades"],
        ["a card by vendor and model", "the log shows " + c("/dev/dri/renderD128") + " and not the card; no per-card table exists. Intel and AMD are the first-version targets "
         "(PIANO.md)"],
        ["NVIDIA", "no run recorded; the first version targets Intel and AMD, NVIDIA later (PIANO.md)"],
        ["4096x2304 and larger canvases", "the declared limit is 3K; the coded limit is 4096x2304; the largest canvas obtained is 3840x2160, the last rung of the page's own size ladder "
         "(" + c("MEASURE_PROBES") + " in " + c("page.html") + ": the page never declares a larger " + c("video.max_size") + ", with any browser; " + c("canvas-limits") + " is not PASS on any desktop for this reason). No frame rate or quality figure at 4096x2304 exists"],
        ["bitrate of the current build", "none printed by the final round. The only bitrate figures in the files read are the phase 9 ones above"],
        ["real networks", "all figures are on loopback; no loss, delay, jitter or throughput measurement of 1.0.0 over a real link is recorded"],
        ["a real phone or tablet as client", "owner's hand test on Samsung DeX (clipboard, audio, video, window resize \"regular\", PIANO.md); no numbers"],
        ["CPU and memory per session", "no per-session CPU or memory figure was found in the PIANO.md, the docs read or the logs read"],
        ["duration of a whole run of all.sh", "only the sum of the time limits, 17 860 s (" + rif("Testing") + ")"],
        ["why GNOME paints 39 fps at 60 Hz", "the figure is measured; no cause is recorded"],
    ], "«TAB» — Where no measurement exists") + \
    tip("A measurement worth adding first, if capacity matters: " + c("check-multiuser.py") + " style runs at 4, 6, 8 and 10 users with the "
        "budget off, on one named card, recording the composition delay of " + c("BUDGET_STRAIN_DELAY_MS") + ". This is a suggestion, not a plan "
        "recorded anywhere.", "Suggestion.")

CHAPTER = ("Performance and capacity", [
    ("How to read the numbers of this chapter", S1),
    ("The test machine and the conditions of the measurements", S2),
    ("Picture, frame rate and sound measured on 17 November 2026", S3),
    ("Session and login timings measured on 17 November 2026", S4),
    ("Capacity: the recorded measurements and what they do not cover", S5),
    ("Limits fixed in the code", S6),
    ("Where no measurement exists", S7),
])
