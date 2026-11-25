"""Chapter 19 — Performance and capacity (Fedora 45). On Fedora 45 no picture, frame-rate or latency figure of the check suite is kept in the tree:
the logs of the rounds are kept outside the tree, not in fedora45/. So this chapter quotes ONLY
(1) the pass counts and the closing times written in PIANO.md and in the problem register docs/REGISTRO-problemi.md (entries F6, F22, F33-F36), each
with its date, (2) the figures recorded in docs/DECISIONS.md (earlier build, with their date) and (3) the constants of the code (src/budget.h,
src/rcp.h, src/rcp.c, src/child.c, src/session.c, src/rootside.c, src/capture.c, src/mutter.c, src/page.html). Nothing was measured while writing it."""
from build import c, h4, note, p, rif, sysf, table, tip, ul, warn

# ── 19.1 ─────────────────────────────────────────────────────────────────────
S1 = p("A number in this chapter is one of three kinds, and each is labelled. <b>Recorded on Fedora 45</b>: a pass count or a time written in "
       + c("PIANO.md") + " or in the problem register (" + c("docs/REGISTRO-problemi.md") + ", entries F6, F22, F33 to F36) for the rounds of 22 to 25 November 2026; it is "
       "quoted with its date. <b>Recorded earlier</b>: written in " + c("docs/DECISIONS.md") + " from a campaign made before Fedora (on Intel hardware, on an earlier build), "
       "quoted with its date and NOT a measurement of this tree. <b>Coded</b>: a constant or default in the source, cited by name; it is a limit or a target, "
       "not an observation.", lead=True) + \
    p("The picture, frame-rate, sound-sync and latency figures that the checks " + c("check-media.py") + " and " + c("check-lifecycle.py") + " can print are not kept in the "
      "tree on Fedora: the logs of the rounds are kept outside the tree. Where a figure that a reader would expect does not exist here, the section says "
      "so (" + rif("Where no measurement exists") + "). What was tried, desktop by desktop, is this: the final round on package <b>h1</b> (23 November 2026, "
      "SELinux enforcing, the Radeon passed through) gave GNOME 52 PASS and one known FAIL (" + c("users-shell-and-environment") + ", the empty SHELL under "
      + c("pkexec") + ") plus 39 PASS for the rest of " + c("all.sh") + ", KDE 76 PASS, XFCE 60 PASS and LXQt 60 PASS (F35). The owner then tried all four desktops by hand on a "
      "real machine booted from a Fedora 45 live stick (25 November 2026); KDE failed with h1 and passed with i1 and then i2, the candidate (F36). Package <b>i2</b> differs from h1 only in the closing of "
      "KDE and one SELinux rule, and was not run again on the other three desktops (decision of the owner, PIANO.md, 25 November).") + \
    note("A measurement made by a check that drives a browser through its debugging interface includes the check's own cost. "
         "The tool's limits are given in " + rif("Testing") + ". A pass count is evidence that a property holds under the "
         "stated conditions, not a benchmark of the product.")

# ── 19.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The rounds of 22 to 25 November 2026 ran on the VM bench of " + c("server/vm-radeon.sh") + " (" + rif("The VM bench") + "), and the hand tests of 25 November "
       "on a real machine. There is no container bench on Fedora.", lead=True) + \
    ul([
        "<b>Machine.</b> A QEMU/KVM virtual machine with UEFI, installed from the contents of the Fedora 45 live image of the desktop (images " + c("Fedora-*-Live-45-1.4") + "), "
        "with " + c("CPUS=4 MEM=5G DISKSZ=40G") + " (" + c("server/vm-radeon.sh") + "); the build VM " + c("costruzione") + " has 8 CPUs and 6 GB. SELinux is enforcing, with the "
        "policy as the package leaves it (no <i>permissive</i> mode, the <i>dontaudit</i> rules of the base policy in place: F33). The server's AMD Radeon is passed through by "
        + c("vfio-pci") + "; the machine sees that card and no other, and only one machine at a time can hold it. The model of the card is not written in the files read for this chapter. "
        "The time to power such a machine on or off is a property of the bench, not of the product, and is not reported.",
        "<b>Bench switches.</b> " + c("RX_BANCO=vm") + " selects the VM bench (ports 8851 to 8854 for the four desktops, " + c("prove/lib.py") + "); " + c("RX_TEMPO") + " is 2 by "
        "default on that bench (" + c("prove/all.sh") + ") and doubles every deadline of the checks. A figure that the product itself prints is not changed by it; a deadline "
        "that the check waits for is doubled. The checks reach the machine through the user-mode network of QEMU (" + rif("The VM bench") + ").",
        "<b>Client.</b> A real browser on the dev server driven by its debugging interface, in a headless compositor. The versions of Chrome and Firefox of the Fedora bench are "
        "not written in the files read, so they are not given here. In the KDE VM, Chromium was installed by hand (F33). The path to the machine is the virtual network of the host: nothing "
        "here says anything about bandwidth, loss or delay of a real link.",
        "<b>Codec.</b> On Fedora 45 the H.264 encoding on the video card is required, and the drivers come from RPM Fusion (decision D1: <code>mesa-va-drivers-freeworld</code>); the test "
        "VMs start from the snapshot " + c("codec") + " (clean installation plus those codecs). On the delivery machines of 23 November, " + c("--encoding-test h264") + " was "
        "hardware, through " + c("h264_vulkan") + " on the Radeon (F35); on the real machine of 25 November the encoding test also succeeded on the Intel card of that machine (PIANO.md). "
        "HEVC in the browser was not tried on Fedora.",
        "<b>What a virtual machine without the Radeon cannot do.</b> Without the card there is no H.264 encoding, so the remote desktop is not admitted (F18); everything that needs a "
        "live remote desktop waits for the VM that has the Radeon.",
    ])

# ── 19.3 ─────────────────────────────────────────────────────────────────────
S3 = p("<b>Not measured on Fedora.</b> The checks " + c("screen-updates") + ", " + c("video") + ", " + c("codec") + " and " + c("two-sessions-budget")
       + " of " + c("check-media.py") + " ran in the rounds (they are part of the 39 PASS of GNOME), but their figures (values seen out of sent, frames per second painted, sound-to-picture "
       "error, sharpness) are in logs that are not in the tree, and this manual does not carry over the figures of another distribution: the bench, the card, the compositor and the "
       "client are not the same.", lead=True) + \
    h4("What is coded, and so holds whatever the distribution") + \
    ul([
        "<b>Sound lags the picture by a declared cushion.</b> The audio cushion " + c("AUDIO_BUFFER_MS") + " is 250 in " + c("page.html") + ", a declared price (the comment in the page "
        "explains why 60 ms produced gaps). The check does not judge lip-sync: it prints the lag and leaves the judgement to the owner.",
        "<b>The two-session check is a regression test, not a capacity test.</b> The budget knob is off by default (" + c("--budget-mpixel-s 0.0") + " with " + c("--session-cap 10 --reserve 0.50")
        + "); the rule being tested is that whoever is inside is not degraded.",
        "<b>The 60 frames per second ceiling</b> is " + c("MOTION_FPS") + " in " + c("child.c") + ".",
    ]) + \
    h4("KDE: the lost frame, a property of the code") + \
    p("The code has a mechanism that bears on the picture of KDE, described here only as a coded limit: " + c("capture_watch_sequence()") + " and " + c("capture_frame_lost()")
      + " in " + c("capture.c") + " watch the numbering of the buffers that KWin delivers; a gap forces a frame marked \"all changed\" and, after " + c("LOST_QUIET_MS") + " = 200 ms without an image, "
      "a poke through " + c("kwin_poke()") + " (in " + c("kwin.c") + "), at most " + c("LOST_POKES_MAX") + " = 10 times in a row, with a window of " + c("SEQ_WINDOW")
      + " = 600 buffer numbers (the mechanism is explained in " + rif("The lost frame (KWin)") + "). The comments of " + c("capture.c") + " record measurements made earlier, "
      "on a KWin 6.6 running inside a labwc of the project (a window left halfway through an animation for 18 to 26 s; 68 pokes on a still desktop). On Fedora KWin 6.8 runs alone "
      "(" + c("--virtual") + ") and that behaviour has <b>not been measured</b>: it is a limit of the code, not a result, and whether the buffer source of KWin 6.8 still loses frames "
      "is not known.")

# ── 19.4 ─────────────────────────────────────────────────────────────────────
S4 = p("The timings below are the ones written in the register and in the plan for Fedora 45, with their date. The refusal floor is the only coded one.", lead=True) + \
    table(["Timing", "Value", "Source"], [
        ["login refused (wrong password or unknown name): constant floor, so that the two are indistinguishable", c("REJECT_FLOOR") + " = 2500 ms (a coded floor; the figure measured on Fedora was not recorded)", c("rcp.c")],
        ["remote desktop closed by a local login, GNOME (gdm), virtual machine", "1 to 2 s; a local login with no remote desktop takes 0.4 s (0.3 s without the hook)", "F6, 21 Nov 2026"],
        ["the same, KDE (plasmalogin), XFCE (lightdm), LXQt (sddm), virtual machines", "1 to 2 s on all three", "F9, F22, 21-22 Nov 2026"],
        ["the same, real machine from the live stick: XFCE (lightdm)", "orderly close in 1.7 s", "PIANO.md, 25 Nov 2026"],
        ["the same, real machine from the live stick: LXQt (sddm)", "orderly close in 0.7 s", "PIANO.md, 25 Nov 2026"],
        ["the same, KDE, virtual machine, package i2, no program open", "2.9 s", "PIANO.md, 25 Nov 2026"],
        ["the same, KDE, virtual machine, package i2, Konsole + top + an editor with unsaved text", "forced close at 5.03 s; everything stopped 0.54 s later; the hook freed at 5.87 s", "PIANO.md, 25 Nov 2026"],
        ["the same, KDE, virtual machine, ten healthy programs", "orderly close in 1.1 s, no forced close", "PIANO.md, 25 Nov 2026"],
        ["the same, KDE, real machine from the live stick, package i1 (wait of 10 s)", "forced close at 10.05 s; everything stopped 0.56 s later; hook freed at 10.9 s", "F36, 25 Nov 2026"],
        ["the same, KDE, real machine from the live stick, package i2 (wait of 5 s)", "forced close at 5.04 s; hook freed at 5.9 s; 0 SELinux refusals, 0 core dumps", "F36, PIANO.md, 25 Nov 2026"],
    ], "«TAB» — Closing times of a remote desktop when a local login arrives, as recorded on Fedora 45") + \
    ul([
        "<b>Why KDE has its own wait.</b> A normal close of the desktop (" + c("org.kde.Shutdown.logout") + ") waits without a limit for a program that does not close by itself or asks "
        "for confirmation. For a local login the forced close of KDE now stops " + c("graphical-session.target") + " after " + c("KDE_PRELOCAL_ORDERLY_MS") + " = 5000 ms ("
        + c("session.c") + "), applied only when the forced close is armed; the general wait is " + c("WAIT_EXIT_MS") + " = 10000. The cost, declared to the owner: a healthy close that "
        "took between 5 and 10 s now gets cut by the forced one (PIANO.md, 25 Nov 2026). Slow-closing programs and a close by abandonment were not tried.",
        "<b>The root side's own deadlines</b> for a held local login are " + c("PL_GRACE_MS") + " = 13000, " + c("PL_CEIL_MS") + " = 20000 and " + c("PL_HOLD_MS") + " = 10000 in "
        + c("rootside.c") + " (" + rif("The local-login hold") + ").",
        "The child may tell the clients \"the session is over\" before it dismantles its stage (" + c("session_over_early()") + " in " + c("child.c")
        + ", only on a certain death and never on KDE).",
        "A restart of the service closes the remote desktops (DECISIONS-11 §11.56): the package scriptlet comment that says the desktops stay alive on an update contradicts it "
        "(" + rif("Contradictions between code, comments and documents") + ").",
        "The timings of the other checks (the 29 s and 90 s clocks, the 11 s of the network drop, the 6 s of two users) were measured on Ubuntu and are not carried over: on Fedora "
        "those checks passed in the rounds, but their figures are not written in the tree.",
    ])

# ── 19.5 ─────────────────────────────────────────────────────────────────────
S5 = p("The question \"how many users can one machine serve\" has no measured answer for this tree. What exists is (a) the recorded "
       "capacity campaign of August 2026, made on an earlier build and on Intel hardware, and (b) the most users any check attaches at once on Fedora.", lead=True) + \
    h4("Recorded earlier: phase 10, 24 Aug 2026, on the earlier build") + \
    p("Source: " + c("docs/DECISIONS.md") + " §4.6-septies and §4.6-nonies (both are in " + c("fedora45/docs/") + "). The campaign predates the 30 September 2026 change in which ffmpeg "
      "left the product and encoding moved to libva and Vulkan Video directly (comment of " + c("src/Makefile") + ", DECISIONS §10.25), so "
      "the numbers are those of another encoder path. The hardware was the Intel integrated card of the dev server; §4.6-septies calls it a "
      "UHD 730, a name that DECISIONS-11 §11.21 corrected to UHD 770. The campaign is independent of the distribution and of the package, and was not repeated on Fedora 45.") + \
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
         "REMOTIX for Fedora, and a figure without its hardware must not be quoted at all (DECISIONS §4.6-septies).") + \
    h4("Recorded earlier: bandwidth and audio traffic, phase 9") + \
    ul([
        "DECISIONS §3.1-ter: the worst case on the real path (a client over a throttled link) asked for 21.5 to 23.1 Mbit/s and was held "
        "with all 7,125 frames delivered and painted, one keyframe, no abandonment.",
        "DECISIONS §3.1-septies: audio silence suppression cut the traffic of a still screen by 102 times (557.6 to 5.5 kbit/s).",
        "Both are on an earlier build and an earlier page; they are context, not a specification of this release.",
    ]) + \
    h4("Recorded on Fedora 45: the most users tried at once") + \
    p("On GNOME, " + c("two-users") + " and " + c("three-users") + " of " + c("check-multiuser.py") + " and " + c("tap-click-portrait") + " of " + c("check-phone.py") + " were FAIL in "
      "round f1 (23 November 2026) and are PASS after the cure of the first pointer movement (F34, package g6): " + c("two-users") + ", " + c("three-users") + " and "
      + c("same-user") + " PASS and the whole of " + c("check-phone.py") + " PASS; in the final round on h1 the rest of " + c("all.sh") + " on GNOME is 39 PASS (F35). Every check runs with the "
      "default cap of " + c("RCP_SESSION_CAP") + " = 10 sessions in force, but none fills it. The case " + c("session-cap") + " (the cap lowered to 2) was not verified on Fedora. On the other three "
      "desktops, " + c("check-base.py") + " and " + c("check-input.py") + " ran as 31 PASS each, 0 FAIL (F34); " + c("check-multiuser.py") + " was not run on KDE, XFCE or LXQt.")

# ── 19.6 ─────────────────────────────────────────────────────────────────────
S6 = p("These are properties of the source, not observations. Each names its definition. The constants were read again in this tree.", lead=True) + \
    table(["Limit", "Value", "Where"], [
        ["sessions at once, default (technical)", "10 (administrative cap, not a measure of capacity; configurable with " + c("--session-cap") + ")", c("RCP_SESSION_CAP") + " in " + c("rcp.h")],
        ["composition budget", "off by default (" + c("--budget-mpixel-s") + " 0); reserve 0.5 of the demand kept for whoever is inside",
         c("budget.h") + ", " + c("BUDGET_DEFAULT_RESERVE")],
        ["canvas size accepted (technical)", "320 to 4096 wide, 240 to 2304 high", c("rootside.c") + "; " + c("RCP_CANVAS_MAX_W") + " and " + c("RCP_CANVAS_MAX_H") + " in " + c("rcp.h")],
        ["frame rate of a stage", "60 frames per second at most", c("MOTION_FPS") + " in " + c("child.c")],
        ["minimum of the quality ladder (SPECS)", "480p, 25 fps, 24 bit (a guarantee, not a goal)", c("docs/SPECS.md") + " §3.1"],
        ["target of the specification", "4K, 60 fps, 10 bit per channel", c("docs/SPECS.md") + " §3.1 (a target of the specification, not a limit of the program)"],
        ["frame ceiling on the video stream", "16 MiB; above it the frame is re-encoded smaller, not sent", c("V_CAP") + " in " + c("rcp.c") + ", " + c("FRAME_MAX") + " in " + c("child.c") + ", RCP §6.2"],
        ["audio cushion", "250 ms", c("AUDIO_BUFFER_MS") + " in " + c("page.html")],
        ["refusal floor for a wrong password", "2500 ms", c("REJECT_FLOOR") + " in " + c("rcp.c")],
        ["ban counters", "5 per user and address, 20 per address, 30 per IPv6 /48; windows 300, 300 and 600 s; bans of 15 min, 1 h, 12 h",
         c("LIMIT") + ", " + c("WINDOW_MS") + ", " + c("LADDER_MS") + " in " + c("rcp.c")],
        ["a child told to close counts as closing", c("CLOSING_GRACE_MS") + " = 30 000 ms", c("child.c")],
        "Added or relevant on Fedora 45",
        ["lost-frame watch of KWin", c("LOST_QUIET_MS") + " 200 ms, " + c("LOST_POKES_MAX") + " 10, " + c("SEQ_WINDOW") + " 600", c("capture.c")],
        ["one call to Mutter in the scale correction", c("WAIT_CALL_MS") + " = 15 000 ms per call; the child tries to bring the monitor scale back to 1 once, with three calls at most, "
         "so about 45 s in the worst case before it gives up and refuses the stage with 0x0E (comment in " + c("mutter.h") + "); not tried again with GNOME 51",
         c("mutter_scale_to_one()") + " in " + c("mutter.c")],
        ["wait of the orderly close of KDE for a local login", c("KDE_PRELOCAL_ORDERLY_MS") + " = 5000 ms, against " + c("WAIT_EXIT_MS") + " = 10 000 ms in the other cases", c("session.c")],
        ["root-side deadlines of a held local login", c("PL_GRACE_MS") + " 13 000 ms, " + c("PL_CEIL_MS") + " 20 000 ms, " + c("PL_HOLD_MS") + " 10 000 ms", c("rootside.c")],
        ["sweep of KDE compositors that no session holds", c("KDEHOST_SWEEP_MS") + " = 45 000 ms", c("rootside.c") + ", " + c("child.c")],
    ], "«TAB» — Limits fixed in the code") + \
    p("The constants of the first thirteen rows are the same as on Ubuntu 26.04 (the diff of " + c("rcp.h") + ", " + c("budget.h") + " and " + c("rcp.c") + " against the Ubuntu tree is empty); "
      "the rows after the group line are specific to this tree or were re-read for it.")

# ── 19.7 ─────────────────────────────────────────────────────────────────────
S7 = p("This list is deliberate: a manual that stays silent about a missing measurement invites a reader to invent one.", lead=True) + \
    table(["Not measured", "What is known instead"], [
        ["capacity per number of users on this release", "the recorded campaign on the earlier build (above); two and three users attached together on GNOME (PASS after F34). "
         "No run that fills the default cap of 10 and no search for the point where service degrades"],
        ["picture, frame rate, sound sync and latency on any of the four desktops", "no figure is kept in the tree: the four desktops passed their rounds on h1 (GNOME, XFCE, LXQt) and i1/i2 (KDE), "
         "but the performance figures, if the logs hold them, are kept outside the tree"],
        ["a card by vendor and model", "the Radeon through the VM bench, and, on the real machine of 25 November, an Intel card and a Radeon from the live stick, where only the encoding test "
         "(" + c("--encoding-test h264") + ") was reported on the Intel card; the functional suite was never run on the Intel card. No per-card table exists"],
        ["NVIDIA", "not run again on Fedora 45 (measured on Ubuntu 26.04, 5–6 Oct 2026)"],
        ["4096x2304 and larger canvases", "the coded limit is 4096x2304; " + c("canvas-limits") + " was not verified on Fedora. No frame rate or quality figure at those sizes exists"],
        ["HEVC in the browser", "not tried on Fedora; H.264 is the only codec tried"],
        ["bitrate of the current build", "none recorded. The only bitrate figures in the files read are the phase 9 ones above"],
        ["real networks", "all figures are on a virtual network; no loss, delay, jitter or throughput measurement over a real link is recorded"],
        ["CPU and memory per session", "no per-session CPU or memory figure was found in the plan file, the register, the docs read or the logs read"],
        ["duration of a whole run of all.sh", "not recorded on Fedora; the sum of the time limits is multiplied by " + c("RX_TEMPO") + " on the VM bench (" + rif("Testing") + ")"],
    ], "«TAB» — Where no measurement exists") + \
    h4("A real phone as client: small stutters in the video (a case seen on Ubuntu)") + \
    p("On Ubuntu the owner reported small stutters when playing a video in the remote GNOME session from Chrome on an Android phone; the entry of the register of that tree (E4) records "
      "a measurement of 40 s of video towards the phone, but its raw logs were not found, and its figures are not carried over here. It was <b>not reproduced on Fedora</b>: the owner, on 21 November "
      "2026, from an Android phone on GNOME, described the 1440p video as very smooth (PIANO.md). It is an open, non-blocking case of the Ubuntu tree (" + rif("Fedora: open points") + "), not a benchmark.") + \
    tip("A measurement worth adding first, if capacity matters: " + c("check-multiuser.py") + " style runs at 4, 6, 8 and 10 users with the "
        "budget off, on one named card, recording the composition delay of " + c("BUDGET_STRAIN_DELAY_MS") + ". These are suggestions, not plans "
        "recorded anywhere.", "Suggestion.")

CHAPTER = ("Performance and capacity", [
    ("How to read the numbers of this chapter", S1),
    ("The test machine and the conditions of the measurements", S2),
    ("Picture, frame rate and sound: what is and is not measured", S3),
    ("Session and login timings recorded on Fedora 45", S4),
    ("Capacity: the recorded measurements and what they do not cover", S5),
    ("Limits fixed in the code", S6),
    ("Where no measurement exists", S7),
])
