from build import arrow, box, c, fig, h4, note, p, path, rif, table, text, tip, ul, warn, zone

# ── 1 ───────────────────────────────────────────────────────────────────────
FAMILIES = fig(
    zone(20, 12, 860, 118, "The compositor of the user's session (started by REMOTIX, one per user)")
    + box(40, 46, 250, 66, "Mutter (GNOME)", "gnome-shell --headless --no-x11", "navy")
    + box(325, 46, 250, 66, "KWin (KDE Plasma)", "nested in a screenless labwc", "navy")
    + box(610, 46, 250, 66, "labwc (XFCE, LXQt)", "WLR_BACKENDS=headless", "navy")
    + box(40, 170, 250, 56, "mutter.c", "D-Bus ScreenCast + RemoteDesktop", "blue")
    + box(325, 170, 250, 56, "kwin.c", "zkde_screencast_unstable_v1", "blue")
    + box(610, 170, 250, 56, "wlroots.c", "zwlr_screencopy_manager_v1", "blue")
    + box(40, 262, 535, 56, "PipeWire node", "frames are pushed: capture_start(node)", "dark")
    + box(610, 262, 250, 56, "No PipeWire", "capture_start_wlr(): frames are asked for", "dark")
    + box(160, 356, 580, 60, "capture.c: one contract", "capture_take() · capture_stopped_free() · counters", "light")
    + arrow(165, 114, 165, 168) + arrow(450, 114, 450, 168) + arrow(735, 114, 735, 168)
    + arrow(165, 228, 165, 260) + arrow(450, 228, 450, 260) + arrow(735, 228, 735, 260)
    + arrow(307, 320, 380, 354) + arrow(735, 320, 640, 354)
    + text(450, 448, "child.c reads the same interface on all four desktops", 11, "#475569"),
    900, 460, "«FIG» — Three compositor families, two directions (push and pull), one capture contract")

S1 = p("REMOTIX does not grab a physical screen. Every user has a desktop session of their own, started by "
       "REMOTIX with a compositor that has no monitor (" + rif("Startup and life cycle") + "), and the capture "
       "reads that compositor's virtual output. On Ubuntu 26.04 there are three compositor families behind the four "
       "desktops (Ubuntu with GNOME 50, Kubuntu with KDE Plasma 6.6, Xubuntu with XFCE, Lubuntu with LXQt), and they deliver frames in two opposite directions. GNOME and KDE <i>push</i> frames through a "
       "PipeWire node; labwc, the compositor REMOTIX runs under XFCE and LXQt, has no node and every frame is "
       "<i>asked for</i> with the wlroots screencopy protocol. A single module, " + c("capture.c") + ", hides the "
       "difference from " + c("child.c") + ".", lead=True) + FAMILIES + \
    table(["", "GNOME", "KDE Plasma", "XFCE and LXQt"], [
        ["Compositor", "Mutter inside " + c("gnome-shell --headless --no-x11 --mode=<session>") + " (drop-in written by " + c("session.c") + "; <i>session</i> is " + c("ubuntu") + " on a stock Ubuntu)",
         "KWin, born <i>nested</i> as a full-screen window of a screenless labwc, REMOTIX's own build of it (" + c("kwin_nested_alive()") + ")",
         "labwc with " + c("WLR_BACKENDS=headless") + " and " + c("WLR_LIBINPUT_NO_DEVICES=1") + " (" + c("session.c") + ")"],
        ["Capture file", c("mutter.c") + " then " + c("capture.c"), c("kwin.c") + " then " + c("capture.c"),
         c("wlroots.c") + " through " + c("capture_start_wlr()")],
        ["Interface used", c("org.gnome.Mutter.RemoteDesktop") + " and " + c("org.gnome.Mutter.ScreenCast")
         + " on the user's session bus", c("zkde_screencast_unstable_v1") + " on the user's Wayland socket",
         c("zwlr_screencopy_manager_v1") + " (v3), " + c("zwlr_output_manager_v1") + ", " + c("zwp_linux_dmabuf_v1")],
        ["How frames arrive", "Pushed: PipeWire node from " + c("RecordVirtual"), "Pushed: PipeWire node from "
         + c("stream_output"), "Pulled: " + c("capture_output") + ", " + c("copy") + ", " + c("ready") + " for every frame"],
        ["Virtual output", "Created by " + c("RecordVirtual") + " every time the stage is mounted",
         "KWin's only output, the size of the labwc output that hosts it", "The headless output of labwc"],
        ["Access gate", "None beyond the user's own D-Bus session (direct interfaces, no portal)",
         "A " + c(".desktop") + " file that lists the protocol in " + c("X-KDE-Wayland-Interfaces"),
         "None: the only gate is the uid of the socket's folder"],
        ["Resize", "Live: " + c("pw_stream_update_params()"), "The stage is dismantled, labwc's output is resized, KWin's "
         "output follows, the stage is remounted", "Live: " + c("zwlr_output_manager_v1") + " changes the output"],
        ["Zero copy (DMA-BUF)", "Yes, negotiated with modifiers", "Yes, negotiated with modifiers",
         "Yes, into GBM buffers owned by REMOTIX (slabs)"],
        ["Pointer shape", "Mutter cursor metadata (" + c("cursor-mode") + " = 2)", "KWin cursor metadata carrying an encoded pixel",
         "Pointer drawn into the image; a 3×3 probe reads an encoded pixel"],
    ], "«TAB» — The capture, desktop by desktop, on Ubuntu 26.04") + \
    p("Which family is in use is decided once per process by " + c("desktop_session()") + " and, for the labwc family, "
      "by " + c("session_on_wlroots()") + " (both in " + c("session.h") + "; see " + rif("The four desktops") + "). In "
      + c("child.c") + " the stage mount tests " + c("session_on_wlroots()") + " first, then the KDE case, then GNOME, and "
      "opens the capture with " + c("capture_start_wlr()") + " or " + c("capture_start()") + " accordingly. "
      "There is no per-compositor switch inside " + c("capture.c") + ": where a compositor cannot do something, the "
      "behaviour is the same for everyone that cannot.") + \
    note("two different labwc programs are in play. XFCE and LXQt run the <i>distribution's</i> labwc (0.9.3-1 in Ubuntu's "
         "universe), a <i>Recommends</i> of the package, not a hard dependency (" + c("debian/control") + "); without it those "
         "two desktops cannot start, and since 18 Nov 2026 the server refuses the login with the reason 0x0E before a child "
         "is born (" + c("session_missing_component()") + " in " + c("session.c") + ", called from " + c("main.c") + "; "
         "the check exists only for XFCE and LXQt). KDE runs REMOTIX's <i>own</i> labwc, " + c("/usr/libexec/remotix/labwc")
         + ", shipped inside the package (labwc 0.9.3 with wlroots 0.19.2 and a small patch, linked statically). If that file "
         "is missing KDE still starts, with KWin in its <code>--virtual</code> mode, as a declared fallback. Both cases are in "
         + rif("KDE: the KWin screencast protocol and the nested KWin") + ".", "Two labwc programs.")

# ── 2 ───────────────────────────────────────────────────────────────────────
S2 = p("The mandate written at the top of " + c("capture.h") + " is to deliver a frame with the <i>declared</i> buffer "
       "type, never a deduced one. Three rules from the earlier REMOTIX generations survive in the code, and each one "
       "exists because breaking it produces no error at all.", lead=True) + \
    table(["Rule", "What the code does", "Why"], [
        ["The stride is read, never computed", "The stride comes from the buffer chunk. A frame with "
         + c("stride == 0") + " is discarded and counted (" + c("stride_zero") + ") instead of being given "
         + c("width × 4") + ". " + c("dimcheck.h") + " (" + c("dim_stride_ok()") + ", " + c("dim_object_size()")
         + ", " + c("dim_frame_ok()") + ") does the arithmetic in 64 bits.",
         "A producer may pad rows, and a wrong stride gives a slanted image that looks almost right. At "
         "1920×1080 the measured stride was 7680, which is exactly " + c("width × 4") + ", so the rule has to be "
         "written down before the day it stops matching."],
        ["The buffer type is asked in two places", "DMA-BUF is requested both in the " + c("modifier")
         + " field of the format (" + c("MANDATORY | DONT_FIXATE") + ") and with the " + c("SPA_DATA_DmaBuf")
         + " bit of " + c("SPA_PARAM_Buffers") + "; the bit is set only if the card route was requested.",
         "With only one of the two the negotiation still succeeds and buffers keep arriving in memory: no error, no "
         "log line, no zero copy."],
        ["The frame rate is declared as zero", c("framerate = 0/1") + " plus " + c("maxFramerate")
         + " up to the rate the caller passes (" + c("MOTION_FPS") + " = 60 in " + c("child.c") + ").",
         "It means «send a frame when something changes». On a still desktop nothing arrives, and that is a "
         "result, not a fault."],
    ], "«TAB» — The three rules of the capture") + \
    p("The negotiated facts are exposed in " + c("CaptureDelivery") + " (read with " + c("capture_delivery()")
      + "), in four groups that downstream code reads instead of recomputing:") + \
    ul(["<b>buffer type</b>: the requested type (" + c("requested_route") + ", " + c("buffer_requested") + ") and the "
        "declared one (" + c("buffer_declared") + ") are separate fields, so what arrives is the answer to the question "
        "REMOTIX asked, not a discovery about the compositor;",
        "<b>bits per channel</b>: from the negotiated format, and 0 means unknown;",
        "<b>geometry</b>: size, the stride read from the chunk (" + c("stride_read") + " says whether it is a fact or "
        "still empty) and the DRM modifier;",
        "<b>colour</b>: range, matrix, transfer and primaries as the producer declares them, «not declared» included, "
        "plus what REMOTIX measures on the pixels (minimum and maximum per channel, black, uniform)."]) + \
    p("The pixel measurement (" + c("measure_pixels()") + ") is diagnostic only. It runs on the first frame and then at "
      "most every " + c("PIXEL_SCAN_EVERY_MS") + " = 500 ms. " + c("measured_pixels") + " sits beside the results "
      "so that «not black» and «not looked at» cannot be confused: on an unmeasured frame " + c("nero") + " and "
      + c("uniform") + " are false, and false would otherwise read as «it is not black». The comments of "
      + c("capture.h") + " give the reason for the cadence as a measured cost of 5.34 ms out of a 21.6 ms path "
      "(25 %) when the scan ran on every frame; that figure comes from the comment, not from a run of this tree.") + \
    table(["Outcome of " + c("capture_take()"), "Meaning", "What the caller does"], [
        [c("CAPTURE_TAKE_DONE"), "A frame was copied into memory", "Encode from " + c("pixel")],
        [c("CAPTURE_TAKE_PIXEL_ELSEWHERE"), "A frame on the GPU path: " + c("pixel") + " is NULL and "
         + c("fd") + ", " + c("offset") + ", " + c("stride") + ", " + c("modifier") + " describe a DMA-BUF that is "
         "<b>retained</b>", "Encode from the descriptor, then call " + c("capture_stopped_free()")],
        [c("CAPTURE_TAKE_ZERO"), "The stream was active for the whole wait and nothing arrived (a still desktop)",
         "Nothing: it is a legitimate zero"],
        [c("CAPTURE_TAKE_FAULT"), "The stream was never active, or it has died", "Report, remount the stage"],
    ], "«TAB» — Zero and failure are different outcomes") + \
    warn("the PipeWire callbacks run on PipeWire's own real-time thread (" + c("pw_thread_loop") + "). Nothing may wait "
         "inside them, " + c("capture_stop()") + " must not be called from the end callback, and the pixels live only for "
         "the duration of the callback: the copy into REMOTIX's buffer is made there, and frames that arrive while nobody "
         "is waiting are only counted.", "Real-time thread.") + \
    p(c("CaptureStopped") + " also carries the timing of the stretch that precedes the encoder, in microseconds of "
      + c("CLOCK_MONOTONIC") + ": " + c("arrival_us") + " (when the frame was parked), " + c("copy_us") + " (the "
      + c("memcpy") + " in the callback), " + c("alloc_us") + " (0 when the slot buffer was reused), " + c("in_slot_us")
      + " (how long the frame waited for a taker) and " + c("measure_us") + ". They are not filled for a frame "
      "delivered to the " + c("on_frame") + " callback, where there is no slot and no copy.") + \
    p("The damage regions (" + c("SPA_META_VideoDamage") + ") are information about how much changed, not a condition "
      "for reading the buffer. The comment of " + c("capture.h") + " records a measurement of 12 Aug 2026 (Mutter 48.7 on Debian, "
      "memory path, 410 frames) in which damage was partial on every frame and the buffer was nevertheless whole in "
      "every one. At most " + c("CAPTURE_DAMAGE_MAX") + " = 16 regions travel with a frame; beyond that the frame counts "
      "as entirely damaged, the safe case. " + c("damage_classify()") + " tells three cases apart: damage absent (the "
      "producer says nothing, the frame counts), empty (the producer declares that nothing changed) and present.")

# ── 3 ───────────────────────────────────────────────────────────────────────
SEQ = fig(
    "".join(text(x, 40, t, 12, "#003a90", "700") for x, t in
            [(110, "mutter.c"), (330, "RemoteDesktop"), (560, "ScreenCast"), (790, "PipeWire")])
    + "".join(f'<line x1="{x}" y1="50" x2="{x}" y2="372" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 4"/>'
              for x in (110, 330, 560, 790))
    + arrow(115, 72, 325, 72, label="1  CreateSession → read SessionId")
    + arrow(325, 104, 115, 104, "#475569", True, label="ConnectToEIS (input channel)")
    + arrow(115, 136, 555, 136, label="2  CreateSession(remote-desktop-session-id)", lx=330)
    + arrow(115, 168, 325, 168, label="3  Session.Start (only now)")
    + arrow(115, 200, 555, 200, label="4  RecordVirtual(cursor-mode=2, is-platform)", lx=330)
    + arrow(115, 232, 555, 232, "#475569", True, label="subscribe PipeWireStreamAdded first", lx=330)
    + arrow(115, 264, 555, 264, label="5  Stream.Start", lx=330)
    + arrow(555, 296, 115, 296, "#475569", True, label="signal: PipeWire node id", lx=330)
    + arrow(115, 328, 785, 328, label="capture_start(node): format proposal, buffers, metadata", lx=450)
    + arrow(785, 360, 115, 360, "#475569", True, label="streaming: the virtual monitor now exists", lx=450),
    900, 384, "«FIG» — The obligatory Mutter sequence; any permutation fails with a different error")

S3 = p("On GNOME REMOTIX talks to Mutter's direct D-Bus interfaces, " + c("org.gnome.Mutter.RemoteDesktop") + " and "
       + c("org.gnome.Mutter.ScreenCast") + ", on the user's session bus, not to " + c("xdg-desktop-portal") + ". The "
       "portal asks permission of a user sitting at the screen, and a headless session has nobody there.", lead=True) + SEQ + \
    p("The order admits no permutation, and each wrong order is punished with a different message that never says "
      "«wrong order»: the comment of " + c("mutter.h") + " records that starting the control session before step 2 gives «Remote desktop session already started» and starting the "
      "capture with " + c("Session.Start") + " gives «Must be started from remote desktop session». Closing follows the same logic in "
      "reverse: " + c("mutter_close()") + " stops the <i>control</i> session and the capture follows it. The PipeWire node "
      "is announced by a signal emitted <i>during</i> " + c("Stream.Start") + ", so " + c("mutter.c") + " subscribes "
      "to " + c("PipeWireStreamAdded") + " before calling it.") + \
    table(["Detail", "Value in the code", "Why"], [
        [c("cursor-mode"), c("CURSOR_METADATA") + " = 2", "The pointer is removed from the pixels and sent as metadata; the "
         "page draws it (" + rif("The RCP/1 protocol") + ")."],
        [c("is-platform"), "true", "The virtual monitor is configured like a real screen."],
        [c("mapping-id"), "A random UUID is sent", "The comment records that Mutter ignores it. The real key is the UUID Mutter "
         "publishes in the stream's " + c("Parameters") + ", read by " + c("mutter_published_mapping_id()") + " for "
         "the input region (" + rif("Input") + ")."],
        ["D-Bus call timeout", c("WAIT_CALL_MS") + " = 15000", "A ceiling on every call."],
        ["Wait for the node", c("WAIT_NODE_MS") + " = 10000", "The node arrives as a signal; without a ceiling a lost signal would wait forever."],
    ], "«TAB» — What RecordVirtual is asked, " + c("mutter.c")) + \
    p("The virtual monitor is mounted by the program every time the stage is mounted, never by configuration: "
      + c("session.c") + " starts " + c("gnome-shell --headless --no-x11") + " without a " + c("--virtual-monitor")
      + " argument, so the session has no monitor until REMOTIX asks for one. Our monitor is identified by "
      "<b>name</b>, never by index or size: " + c("mutter_find_monitor()") + " compares the connectors before and after "
      + c("RecordVirtual") + " and the product name, and if they do not agree on exactly one new monitor the answer "
      "is «unknown», not a guess. It has to be called once the stream is active, because Mutter creates the "
      "monitor when a consumer starts reading.") + \
    warn("with " + c("org.gnome.desktop.interface scaling-factor") + " set to 2 the stream keeps the requested pixels "
         "but the logical monitor gets scale 2.0, and its layout is the coordinate space of input: the pointer would "
         "land elsewhere with no log line. " + c("mutter_our_scale()") + " reads the scale of <i>our</i> monitor; the "
         "child does not take the stage while it is not 1.0. Since 19 Nov 2026 the session first makes the case rare and then "
         "tries to repair it. (1) " + c("session.c") + " writes " + c("org.gnome.desktop.interface scaling-factor") + " = 1 into the "
         "session's dconf database and locks it (" + rif("The four desktops") + "). (2) If the scale read is not 1, the child tries "
         "<i>once</i> " + c("mutter_scale_to_one()") + ": " + c("GetCurrentState") + " then " + c("ApplyMonitorsConfig") + " with "
         "method 1 (temporary), keeping the current mode, passing " + c("layout-mode") + " only when the compositor reports "
         + c("supports-changing-layout-mode") + ", and only in the simple case of one logical monitor, which is ours. The user's "
         + c("monitors.xml") + " is not touched, so a local login finds the user's own scale again. Each of the three synchronous "
         "calls may wait up to " + c("WAIT_CALL_MS") + " = 15 s. (3) If the scale is still not 1, the child sets " + c("p.fatal") + ", "
         "the parent answers the clients with 0x0E (" + c("stage_refused_by_child()") + " in " + c("main.c") + ") and the graphical "
         "session is closed, retried every 10 s if the closing fails. The log lines are «scale back to 1 (temporary, the user's "
         "monitors.xml untouched)» and «the user's scale … is IGNORED in the remote session». The old one-line cure "
         "(" + c("gsettings set … scaling-factor 0") + ") is gone. A scale that cannot be read (−1) is declared and the session "
         "proceeds.", "Scale guard.") + \
    p("The bus connection belongs to the " + c("MutterSession") + " and is lent out by " + c("mutter_bus()") + ": the "
      "clipboard uses the same " + c("RemoteDesktop") + " session, because a second connection would be a second sender "
      "that Mutter does not recognise as the owner. The input channel opened here with " + c("ConnectToEIS") + " and its "
      "recovery " + c("mutter_eis_reattach()") + " are described in " + rif("Input") + ".")

# ── 4 ───────────────────────────────────────────────────────────────────────
S4 = p("On Plasma the capture is a Wayland request to KWin: the private protocol " + c("zkde_screencast_unstable_v1")
       + ", asked for KWin's only output, answers with the id of a PipeWire node. From the node on, the path is the "
       "GNOME one: " + c("capture_start(node)") + ". On Kubuntu 26.04 KWin and Plasma are 6.6.7 (<i>kwin-wayland</i>, in Ubuntu's "
       "universe). The comments of " + c("kwin.c") + " name KWin 6.3.6 for the oldest measurements (October 2026, a nested KWin in "
       "labwc 0.8.3) and KWin 6.6.6 and 6.6.7 for the ones taken on Ubuntu.", lead=True) + \
    table(["Step", "What " + c("kwin_open()") + " does"], [
        ["1", "Opens the user's Wayland socket with " + c("kwin_display_open()") + ": " + c("WAYLAND_DISPLAY")
         + " if it answers, otherwise the first " + c("wayland-N") + " in " + c("XDG_RUNTIME_DIR") + " that answers "
         "(the child is born with an environment composed from scratch)."],
        ["2", "Two round trips: the globals, then the events of the globals just bound (modes, names)."],
        ["3", "If " + c("zkde_screencast_unstable_v1") + " is missing the gate is closed, and the error says which of the two "
         "causes to look at."],
        ["4", "Chooses the first output that has a mode; with none it fails."],
        ["5", c("stream_output(output, POINTER_METADATA)") + " with " + c("POINTER_METADATA") + " = 4; the listener is "
         "attached immediately, because " + c("failed") + " can be sent synchronously."],
        ["6", "Waits for the node at most " + c("WAIT_NODE_MS") + " = 5000 ms; a refusal or a timeout is an error."],
    ], "«TAB» — Opening the KWin stream") + \
    p("<b>The gate.</b> KWin announces " + c("zkde_screencast_unstable_v1") + " only to a client whose executable "
      "(" + c("/proc/<pid>/exe") + ", canonical) appears in the " + c("Exec=") + " line of a " + c(".desktop") + " file that "
      "lists the protocol in " + c("X-KDE-Wayland-Interfaces") + ". The package installs that file as "
      + c("/usr/share/applications/org.kde.remotix.desktop") + " (source " + c("debian/org.kde.remotix.desktop")
      + ", " + c("Exec=/usr/libexec/remotix/remotix") + "), and the server only <i>verifies</i> it at startup with "
      + c("kwin_check_permission()") + " (file present, " + c("Exec=") + " pointing to the running binary, protocol "
      "declared; the failure codes are RX-KDE-001, RX-KDE-002 and RX-KDE-003). The child is an " + c("execve") + " of "
      "the same binary, so it is the process KWin recognises. KWin's environment also needs "
      + c("XDG_MENU_PREFIX=plasma-") + ", or its service index is built empty (" + c("session.c") + ").") + \
    p("<b>The size: KWin nested in labwc.</b> KWin on a machine without a seat cannot use its DRM backend, and the "
      "comments of " + c("kwin.h") + " record that, up to KWin 6.7, its " + c("--virtual") + " backend can neither resize "
      "its output nor create another, while restarting KWin at a new size kills every program that is not Qt. "
      "Therefore KWin is born <i>nested</i>: " + c("session.c") + " writes a drop-in for Plasma's "
      + c("plasma-kwin_wayland") + " user unit whose " + c("ExecStart") + " is " + c("remotix --kwin-nested W H NODE -- "
      "kwin_wayland_wrapper --xwayland --width W --height H --no-lockscreen") + ". That mode of the same binary ("
      + c("kwin_nested_alive()") + ", called from " + c("main.c") + ") starts a labwc without a screen "
      "(" + c("WLR_BACKENDS=headless") + ") in a runtime folder of its own, " + c("$XDG_RUNTIME_DIR/remotix-kwin-host")
      + ", brings its output to W×H, and then becomes the KWin wrapper with " + c("--wayland-display") + " added. KWin "
      "opens one full-screen window in labwc, and its output follows the size of that window. NODE is the render node "
      "chosen by " + c("card_pick_desktop()") + " (" + rif("Video encoding") + "), " + c("pixman") + " when no card can "
      "create a buffer, or " + c("-") + " to let wlroots choose.") + \
    p("<b>The labwc is REMOTIX's own.</b> The path is compiled in: " + c("src/Makefile") + " passes "
      + c("-DREMOTIX_LABWC=\"/usr/libexec/remotix/labwc\"") + " (the make variable " + c("LABWC") + ", which " + c("debian/rules")
      + " sets to the same path), and " + c("kwin_nested_alive()") + " runs the file at that path if " + c("access()") + " finds it "
      "executable. It is not the distribution's labwc: the comments of " + c("kwin.c") + " record that with KWin 6.5 and later the "
      "distribution's labwc leaves KWin on its first frame, because its wlroots never reports KWin's root surface as presented. "
      "The measurement of 18 Nov 2026 (" + c("studio/10-kde-controprova-labwc.md") + ", Ubuntu's labwc against REMOTIX's, 30 s) "
      "counted the " + c("wp_presentation_feedback") + " answers: 0 <i>presented</i> and 755 <i>discarded</i> with the distribution's "
      "labwc, 759 <i>presented</i> and 1 <i>discarded</i> with REMOTIX's. In the first case the clients get frame callbacks with "
      "time 0 and Firefox stops painting (9 intervals out of 11 without a changed pixel). The programs of the session are not "
      "affected otherwise: a terminal still updates in both cases, which is why a first test misled.") + \
    p("The binary comes from " + c("build/labwc-ospite/") + ": " + c("VERSIONS") + " pins labwc 0.9.3 and wlroots 0.19.2 with their "
      "sha256, " + c("fetch.sh") + " downloads and verifies the two archives, " + c("build.sh") + " applies the patch "
      + c("wlroots-0.19.2-remotix-presented-root.patch") + " (a few lines in wlroots' " + "<i>types/scene/surface.c</i>" + ", "
      "so that the root surface is reported as presented), builds with meson with only the GLES2 and pixman renderers "
      "(" + c("-Dwlroots:renderers=gles2") + ") and fails if the result links a shared " + c("libwlroots") + ". wlroots is linked "
      "<i>statically</i>, so the program does not depend on the distribution's wlroots. It exists only for KDE: XFCE and LXQt "
      "keep using the distribution's labwc. Licensing: labwc is GPL-2.0, wlroots is MIT, and the corresponding source of the "
      "shipped binary is published with each release as an archive named " + c("remotix-<version>-labwc-source.tar.gz") + " "
      "(" + rif("The package") + "). That the shipped binary is the one installed was checked on Kubuntu by comparing the "
      "sha256 (round 2, K5).") + \
    p("<b>Reattach at another size.</b> The child dismantles the stage first, because KWin's stream would otherwise "
      "renegotiate to a size the fixed offer refuses and die, then changes labwc's output with " + c("kwin_host_resize()")
      + " (the " + c("zwlr_output_manager_v1") + " road of XFCE and LXQt), waits up to 3 s for KWin's own output to "
      "read the new size, and remounts the stage. Before mounting, " + c("kwin_host_settle()") + " (3 s) waits until "
      "KWin's output has the size the host was asked for, because the comments record that at birth labwc configures "
      "KWin's window more than once and that a capture mounted in between offers a size the stream no longer has "
      "(those timings are from KWin 6.3.6 and labwc 0.8.3). On Kubuntu the reattach checks are green in the round of "
      "18 Nov 2026 (" + c("desktop/reattach-windows-inside") + "). The programs of the session stay.") + \
    table(["What REMOTIX sets", "Why (from the comments of kwin.c)"], [
        ["labwc's own " + c("rc.xml") + " (" + c("HOST_RC") + "), rewritten at every birth and passed with " + c("-C dir")
         + ": every window full screen, matched on " + c("title=\"*\"") + ", no decoration",
         "The mechanism is «KWin's window = labwc's output». A rule on " + c("identifier") + " was recorded as never firing on one "
         "labwc version, so the match is on the title."],
        ["One binding for a key and one for the mouse, each with the single action " + c("None") + "; "
         + c("LABWC_UPDATE_ACTIVATION_ENV=0"),
         "An " + c("rc.xml") + " without bindings makes labwc load its defaults, which start programs (a terminal, the volume "
         "keys); a program of the same user could press them through the virtual-keyboard protocol (rationale cited by "
         "the comment of " + c("kwin.c") + ": DECISIONS.md §10.43)."],
        ["Output refresh 240 Hz (" + c("HOST_MHZ") + ")", "labwc presents on its own clock; at 60 Hz the two clocks drifted and "
         "frames were lost (comment: 59 frames/s with " + c("--virtual") + " against 52–55 nested at 60 Hz)."],
        ["The ticker: a 1×1 transparent surface in labwc's overlay layer, damaged every " + c("TICKER_MS") + " = 16 ms",
         "KWin waits for labwc to present a frame before drawing the next, and labwc presents only when it repaints."],
        [c("KWIN_FORCE_SW_CURSOR=1"), "Nested KWin has a cursor layer that goes to labwc's screen; the software cursor puts "
         "the pointer back into the stream."],
        ["One transparent pixel on top, on the capture's own connection", "Without any window above it, a full-screen "
         "window with the pointer hidden is handed to labwc directly and the picture freezes (comment of " + c("kwin.c") + ")."],
        ["A sidecar that owns " + c("org.freedesktop.ScreenSaver") + " on the user's bus, started beside the ticker",
         "From Plasma 6.4 the Ctrl+Alt+Del shortcut asks " + c("GetActive") + " of that name first (" + rif("Shortcuts the browser keeps")
         + "). KWin runs with " + c("--no-lockscreen") + ", so nobody owned it, the call failed with " + c("ServiceUnknown") + " and "
         "the failure was read as «the screen is locked»."],
    ], "«TAB» — The nested KWin: what REMOTIX sets, and the reason behind each line") + \
    p("<b>The ScreenSaver sidecar.</b> " + c("screensaver_alive()") + " in " + c("kwin.c") + " is a process of its own, forked like the "
      "ticker, that owns the name " + c("org.freedesktop.ScreenSaver") + " on both object paths in use (" + c("/ScreenSaver") + " and "
      + c("/org/freedesktop/ScreenSaver") + ") and never locks anything. " + c("GetActive") + ", the time queries and "
      + c("SimulateUserActivity") + " get a harmless answer; " + c("Lock") + ", " + c("Throttle") + " and " + c("UnThrottle") + " get "
      "the standard error " + c("NotSupported") + "; " + c("Inhibit") + " is forwarded to the same powerdevil call the application "
      "would have made, with the same arguments and cookie, and given back when the caller leaves the bus or calls "
      + c("UnInhibit") + " (measured with VLC: with the name present VLC asks the ScreenSaver first and would not go on after an "
      "error). The name is asked for with DO_NOT_QUEUE: if a real owner is ever there first, the sidecar ends and says so. It dies "
      "with the unit's cgroup at the end of the session and writes nothing in the user's files. Measured with a stand-in on "
      "Plasma 6.6.7 on 18 Nov 2026: the logout prompt appears within 1 s. The sidecar entered the package " + c("unione3") + " (19 Nov 2026), and from that round on " + c("input-chrome/page-cad-chain") + " and "
      + c("input-firefox/page-cad-chain") + " are green on Kubuntu (the earlier red lines of 18 Nov are the defect it cures); in the round of " + c("unione5") + " every line of the Kubuntu box is green (" + c("docs/STORIA-ubuntu-26.04.md") + ").") + \
    p("<b>Without our labwc.</b> When " + c("REMOTIX_LABWC") + " is not executable, " + c("kwin_nested_alive()") + " execs KWin "
      "with " + c("--virtual") + " and prints a declared fallback («our labwc is not installed»); it never falls back to the "
      "distribution's labwc, which would reproduce the defect above. The output keeps the size it was born with, "
      + c("stage_size()") + " captures the size KWin reports (" + c("kwin_measure()") + "), and a reattach at another size "
      "no longer changes the desktop. " + c("kwin_host_exists()") + " is how the child tells the two cases apart.") + \
    p("<b>The «unchanged» filter.</b> The header " + c("unchanged.h") + " records that KWin delivered about 50 buffers a "
      "second for five real changes (3776×2016, Firefox client), roughly 45 of them the same picture. A KWin frame whose "
      "damaged rectangles hold the same bytes as the last frame that went out is not encoded. The filter is switched on "
      "by " + c("capture_skip_unchanged()") + ", which " + c("child.c") + " calls only for KWin, and it is ignored on a "
      "wlroots capture. Its limits, all constants of " + c("unchanged.h") + ":") + \
    table(["Constant", "Value", "Meaning"], [
        [c("UC_MAX_RECTS"), "16", "Damaged rectangles compared"],
        [c("UC_MAX_PIXELS"), "3840×2160 / 4", "Above this damaged area the bytes are not compared and the frame goes out"],
        [c("UC_REFRESH_MS"), "250", "A held-back frame is delivered anyway after this long (KWin can lose a frame's damage), and when frames stop"],
        [c("UC_COST_FIRST") + " / " + c("UC_COST_EVERY"), "30 / 300", "Looks in the first cost window / in every later one"],
        [c("UC_COST_MAX_US"), "3000", "Mean cost of a look above which the filter turns itself off if it held back fewer than 1/" + c("UC_YIELD_DIV") + " (4) of its looks"],
        [c("UC_COST_HARD_US"), "10000", "Mean cost above which it turns itself off whatever it holds back"],
        [c("UC_STRIKES_MAX"), "3", "Switch-offs after which it stays off for the whole capture"],
        [c("UC_REARM_MS"), "5000", "A switch-off for cost re-arms after this long (a new buffer generation also re-arms it)"],
        [c("UC_WAKE_GAP_MS"), "2000", "Minimum distance between two stream restarts asked by a stale held frame"],
    ], "«TAB» — The limits of the «unchanged» filter") + \
    p("<b>Empty damage.</b> KWin 6.6 is recorded as sending about 60 frames a second even on a still screen, with "
      + c("SPA_META_VideoDamage") + " <i>present and empty</i> for the ones that changed nothing. "
      + c("damage_classify()") + " counts them in " + c("empty_damage") + " and the buffer goes back to PipeWire without "
      "being encoded; the frame is never skipped right after the start, after a renegotiated format or a resize, or when its "
      "damage was lost (" + c("deliver_next") + ", " + c("damage_lost") + "). The comment of " + c("capture.c") + " (28 Oct 2026) "
      "records that, counted as «absent», those 53 frames a second of nothing were encoded and the client fell 1–3 s behind. "
      "The comment of " + c("capture.h") + " (19 Nov 2026, KWin 6.6.7) adds that a poke on a still desktop (next section) is answered "
      "with one whole frame whose damage is empty: 68 pokes gave 68 such frames, all dropped.") + \
    p("<b>The cursor.</b> KWin is asked for cursor metadata (mode 4), which makes every pointer movement produce a buffer "
      "without new pixels marked " + c("SPA_CHUNK_FLAG_CORRUPTED") + "; " + c("capture.c") + " discards those and counts "
      "them in " + c("cursor_only") + ". KWin draws the pointer into the image, so the session runs with REMOTIX's encoded "
      "cursor theme (" + rif("The encoded cursor theme") + "), and the child calls "
      + c("capture_cursor_never_hide()") + " so that an empty metadata image is never forwarded as «hidden». The declared "
      "price: on Plasma an application that hides the pointer does not hide it for the viewer.")

# ── 4b ──────────────────────────────────────────────────────────────────────
LOSTSEQ = fig(
    zone(20, 12, 860, 70, "KWin (nested in labwc)")
    + box(40, 36, 250, 36, "numbers every buffer", "spa_meta_header.seq", "navy")
    + box(325, 36, 250, 36, "picture 199, cursor-only 200", "tens of microseconds apart", "navy")
    + zone(20, 104, 860, 70, "PipeWire graph (KWin's stream is the driver)")
    + box(325, 128, 250, 36, "buffer 199 overwritten", "reader not yet woken: an xrun", "dark")
    + zone(20, 196, 860, 150, "capture.c and child.c (REMOTIX)")
    + box(40, 226, 250, 52, "capture_watch_sequence()", "hole 198 → 200: damage_lost, lost_need", "blue")
    + box(325, 226, 250, 52, "capture_frame_lost()", "TRUE after 200 ms of silence", "blue")
    + box(610, 226, 250, 52, "kwin_poke()", "attach, damage 1×1, commit", "light")
    + arrow(450, 74, 450, 102) + arrow(450, 166, 165, 224) + arrow(292, 252, 323, 252) + arrow(577, 252, 608, 252)
    + path([(735, 280), (735, 320), (450, 320), (450, 74)], "#d97706", True, label="KWin draws one frame: the picture arrives", lx=590, ly=312),
    900, 360, "«FIG» — The lost frame: a hole in KWin's buffer numbers, and the request that answers it")

S4B = p("On Kubuntu 26.04 (KWin 6.6.7, PipeWire 1.6.2) a window that had just been opened could stay in the browser half way "
        "through its opening animation, translucent and smaller, for 18 to 26 s, while KWin's own output showed the whole window "
        "from the first second. The cause is a buffer that KWin queued and PipeWire never delivered to REMOTIX. The cure is in "
        + c("capture.c") + ", " + c("child.c") + " and " + c("kwin.c") + ". The reasoning and the measurements are recorded only in "
        "the comments of the code (the end of " + c("capture.h") + ", the head of " + c("capture.c") + ", the call sites in "
        + c("child.c") + "); this section is their documentation. It is not described in " + c("DECISIONS.md") + " or in the "
        "register of problems.", lead=True) + LOSTSEQ + \
    h4("What was measured") + \
    p("KWin numbers every buffer it queues in the " + c("seq") + " field of " + c("spa_meta_header") + ", cursor-only buffers "
      "included. In every stalled run the numbers that reached " + c("on_process") + " had holes: 198, 200, 202, 204, all "
      "cursor-only buffers, and never 199, 201, 203, which were the pictures. The comments mark this as measured (19 Nov 2026), "
      "and the explanation below as read in the sources of KWin 6.6.7 and PipeWire (" + c("[R]") + " in the comments), not "
      "reproduced in isolation.") + \
    h4("Why the buffers are lost") + \
    ul(["<b>Two buffers come close together.</b> In KWin's " + c("screencaststream.cpp") + " the record timer runs "
        + c("record(m_pendingContents)") + " and then clears the pending contents. While " + c("record()") + " draws, an effect that "
        "is still animating schedules the next repaint, which calls " + c("scheduleRecord()") + " again from inside "
        + c("record()") + ": the timer is started at 0 ms and the line after " + c("record()") + " wipes what was asked. The timer "
        "fires with nothing to record, which with the cursor as metadata is a cursor-only buffer. During an animation every picture "
        "is followed, some tens of microseconds later, by a cursor-only buffer.",
        "<b>The first of the two is overwritten.</b> KWin's stream is the <i>driver</i> of the PipeWire graph and every "
        + c("pw_stream_queue_buffer()") + " starts a cycle. A cycle hands the buffer over by plain assignment (" + c("tee_process()")
        + " in " + "<i>impl-port.c</i>" + "), and a cycle started before the reader has run for the previous one is started all the "
        "same (" + c("node_ready()") + " in " + "<i>impl-node.c</i>" + "): the buffer not yet read is overwritten. PipeWire calls it an "
        "xrun; for a video stream it is a frame gone. REMOTIX's reader is a real-time callback that returns in microseconds, but "
        "it must be woken first, and on a busy machine (a session just born) it wakes after the second cycle.",
        "<b>Nothing to tune on the REMOTIX side.</b> The number of buffers and the frame rate do not enter; the transport that "
        "waits for the reader (" + c("node.reliable") + ", PipeWire 1.6) is chosen by the producer."]) + \
    h4("What a lost picture costs") + \
    p("Its damage is lost with it: the next picture declares only what changed after it, so part of the screen stays old. If it "
      "was the last picture of an animation nothing comes after it, and the stream stands at the previous frame until something "
      "else on the desktop changes. A pointer movement does not help, because it brings a cursor-only buffer.") + \
    h4("The cure, in two halves") + \
    table(["Piece", "What it does"], [
        [c("capture_watch_sequence()"), "Called by the child for KWin only (when the stage is mounted, and again in " + c("remount_only_capture()")
         + "); it does nothing on a wlroots capture. It switches on the count: " + c("on_process") + " reads the number of every "
         "buffer before any discard. A number above the last one plus one is a hole: " + c("damage_lost") + " is set, so the next "
         "picture goes out as «all changed» (KWin's buffers are whole frames, so everything lost is inside the next one), and "
         + c("lost_need") + " is set. A header flagged corrupted is KWin giving a buffer back and is not looked at; a number not "
         "above the last is the count starting again, not a hole."],
        [c("capture_frame_lost()"), "Polled by the child's loop. It returns TRUE when " + c("lost_need") + " is set and "
         + c("LOST_QUIET_MS") + " = 200 ms have passed since the last picture or the last poke. Then the child calls "
         + c("kwin_poke()") + ". The request stays up after a poke, because the answer can be lost too: at most one poke every "
         "200 ms until a picture arrives, and a picture arriving clears it. After " + c("LOST_POKES_MAX") + " = 10 pokes in a row "
         "with no picture it stops and says so once, until a picture arrives by itself."],
        [c("kwin_poke()"), "Attaches the 1×1 transparent buffer to the surface REMOTIX keeps on top of KWin's output again, damages "
         "it (a damage with no buffer is not a change) and commits it, under " + c("pixel_lock") + ", then flushes the connection. "
         "KWin answers with one frame. The stream is not restarted, so no input device is recreated, and no input is sent: the guards "
         "on keys or buttons held, needed by " + c("capture_wake()") + ", do not apply."],
    ], "«TAB» — The two halves of the cure") + \
    note("the count rests on «one number per buffer». A producer that counted otherwise would show a hole at every buffer and every "
         "frame would go out as «all changed» with nobody told. If holes are seen in more than half of " + c("SEQ_WINDOW") + " = 600 "
         "buffers (a window of 600, checked at its end), the count is switched off for that capture and the log says so. Measured on "
         "KWin 6.6.7: at most 30 holes in the roughly 200 buffers of a session being born. The mechanism never runs on a still "
         "desktop, because it needs a hole in the numbers to start.", "Safety switch.") + \
    h4("What the log says") + \
    ul(["«the buffers' numbers are watched: a hole in them is a buffer that never arrived…» (area " + c("capture") + ") when the count is switched on;",
        "«a buffer of KWin never arrived and no picture came after it: pixel on top committed again to have one drawn (so far: N holes in "
        "the numbers, N buffers missing, N pokes)», at most once a second;",
        "«a buffer of KWin never arrived, and the pixel on top could NOT be committed again (no pixel, or no connection to KWin)», once "
        "until a poke succeeds again;",
        "«" + "N pokes in a row and no picture from KWin: I stop asking until one arrives by itself»;",
        "«N holes in the numbers of the last 600 buffers … The count is switched OFF for this capture»."]) + \
    h4("What was verified, and what was not") + \
    p("Measured: the holes in the numbers, the 68 pokes on a still desktop answered by 68 frames with empty damage, and the bound of 30 "
      "holes per ~200 buffers at session birth (all in the comments, 19 Nov 2026). The cure was approved by the reviewer on 19 Nov and is inside the package "
      + c("unione5") + ", whose full round on the Kubuntu box is green on every line; the owner's hand tests of 19 Nov (the container machines with " + c("unione5") + ", then the virtual machines and the live image with " + c("unione10") + ") found Kubuntu regular. Not verified: the mechanism on a "
      "machine with a real GPU and a real seat (the measurements are from the test environment), the frequency of the defect after "
      "the cure, and PipeWire releases other than 1.6.2.")

# ── 5 ───────────────────────────────────────────────────────────────────────
S5 = p("On GNOME and KDE the capture is a PipeWire consumer created by " + c("capture_start()") + " on the node the "
       "compositor announced. Everything is declared in the format proposal (" + c("proposal()") + ") and in the "
       "consumption parameters (" + c("consumer_parameters()") + ").", lead=True) + \
    table(["Parameter", "What is proposed", "Why"], [
        ["Pixel format", c("BGRx") + " then " + c("BGRA") + " (" + c("CAPTURE_COLOR_BGRX") + "); the 10-bit request proposes only "
         "the ten-bit formats", "Only what the chain can read is listed. The comments record that Mutter offers only BGRx and "
         "BGRA (read in the source of Mutter 50.1 as well: the virtual stream's table), so the capture is 8 bits per channel on every desktop."],
        ["Size", "A fixed rectangle", "An open range lets the compositor choose, and the comment records that Mutter chooses 1280×720 (" + c("DEFAULT_SIZE") + " is the same in the source of Mutter 50.1)."],
        ["Frame rate", c("0/1") + ", maximum 1 to the requested rate", "Frames on change, never at a fixed rate."],
        ["Modifier (GPU path)", c("DRM_FORMAT_MOD_LINEAR") + " first, then the encoder's modifiers when the card refuses linear, then "
         + c("DRM_FORMAT_MOD_INVALID") + "; flags " + c("MANDATORY | DONT_FIXATE"), "LINEAR first is a lesson recorded from kpipewire "
         "(RadeonSI rejects DCC buffers, iHD accepts them and forces LINEAR internally). INVALID means «you decide and tell me»."],
        ["Buffers", "GPU path: 6 (minimum 4, maximum 8), " + c("SPA_DATA_DmaBuf") + " only. Memory path: 4 (minimum 2), " + c("MemFd")
         + " and " + c("MemPtr"), "On the GPU path REMOTIX retains up to two buffers while the encoder reads them; with four the "
         "producer would be left with two."],
        ["Header metadata", c("SPA_META_Header"), "Sequence number and timestamp of each frame."],
        ["Damage metadata", "16 regions (range 1 to 32)", "The comment records Mutter logging «Not enough buffers (4) to accommodate "
         "damaged regions (6)»: those are region slots, and when they run out the whole frame is declared damaged."],
        ["Cursor metadata", "Up to " + c("CURSOR_META_BYTE(384, 384)"), "Mutter allocates 384×384; the wire limit of 256 is enforced in " + c("cursor.c") + "."],
    ], "«TAB» — The PipeWire negotiation, " + c("capture.c")) + \
    note("when the card refuses a linear render buffer (the comments record NVIDIA with GNOME 50 on Ubuntu 26.04, measured on 6 Oct 2026 "
         "with an earlier version of the code; not run again on this tree, and whether Intel or the Radeon negotiate DMA-BUF modifiers like that card is not verified), the proposal LINEAR + INVALID "
         "ended in «no more input formats». " + c("modifiers_per_route()") + " in " + c("child.c") + " asks "
         + c("vulkanvideo_card_rejects_linear()") + " and only then passes the modifiers the Vulkan encoder can import to "
         + c("capture_modifiers_card()"), "The card that refuses linear.") + \
    p("<b>Buffer generation.</b> Every time PipeWire reallocates its buffers (renegotiation, wake-up) " + c("on_buffer_added()")
      + " and " + c("on_buffer_removed()") + " change a generation counter that travels with every frame (" + c("generation")
      + "). The encoder caches the import of each DMA-BUF, and file descriptor numbers are recycled: a cache keyed on the "
      "descriptor alone would hand the encoder a surface pointing to a freed buffer, an old image with no error. When the "
      "generation changes the cache is dropped.") + \
    p("<b>Retention.</b> On the GPU path the " + c("pw_buffer") + " is held until " + c("capture_stopped_free()") + ", which the "
      "child calls only after the encoder call has returned, that is after the GPU has <i>finished</i> reading and not after "
      "the work was queued. Releasing earlier is the defect recorded in " + c("LESSONS.md") + " §8 (two screens "
      "alternating, no error). " + c("release_held_buffer()") + " gives the buffer back only if its generation is still current.") + \
    h4("What Mutter 50 changes") + \
    p("Read in the source of Mutter 50.1 and not measured by hand (the effect is verified only through the rounds, where "
      + c("desktop/canvas-limits") + " and " + c("media") + " pass on GNOME 50.1): (1) the virtual stream is created with "
      + c("must-drive") + " false and a passive frame clock (" + c("node.supports-request") + " = 2); REMOTIX's consumer is a plain "
      + c("pw_stream") + " and never the driver, so Mutter stays the driver as in earlier versions. (2) After every "
      + c("monitors-changed") + " Mutter publishes the format parameters again, so a resize costs one more renegotiation, "
      + c("capture.c") + " handles format changes already through the buffer generation. (3) The buffer range is 2 to 8 (it was 2 to "
      "16); REMOTIX asks for 6 on the GPU path (minimum 4, maximum 8, " + c("capture.c") + ") and 4 on the memory path, inside the range "
      "but with a narrower margin while the encoder retains two buffers. (4) Every format carries " + c("colorPrimaries") + " = BT709 and "
      + c("transferFunction") + " = GAMMA22 as non-mandatory properties, and Mutter 50 composes SDR with gamma 2.2; "
      + c("colors709.c") + " uses the BT.709 matrix and ignores the transfer tag (" + rif("BT.709 colour conversion") + "). No comparison of images "
      "between Debian and Ubuntu was made.") + \
    h4("Resizing a live stream") + \
    p(c("capture_resize()") + " rebuilds the proposal at the new size and calls " + c("pw_stream_update_params()") + ", without "
      "touching the session or the virtual monitor. It returns " + c("CAPTURE_RECANVAS_REQUESTED") + ", "
      + c("CAPTURE_RECANVAS_UNCHANGED") + " (the size is already in force: renegotiating it would chase its own tail) or "
      + c("CAPTURE_RECANVAS_FAULT") + ". «Requested» is not «done»: the next frame at the new size is the witness. The comments "
      "record that a size the producer cannot hold kills the stream about 2 ms later («no more input formats»); "
      + c("capture_take()") + " looks at the state before waiting, so the failure surfaces in one loop turn instead of a "
      "timeout. The size rule itself (" + c("RCP_CANVAS_MIN_W") + " 320 to " + c("RCP_CANVAS_MAX_W") + " 4096, " + c("RCP_CANVAS_MIN_H")
      + " 240 to " + c("RCP_CANVAS_MAX_H") + " 2304, even sides, larger requests reduced; the declared limit of the product is 3K) lives in " + c("rcp_size_allowed()")
      + " (" + rif("The RCP/1 protocol") + ").") + \
    h4("Waking a still desktop") + \
    p("A Wayland compositor delivers only when the scene changes, and a desktop just started is still. Wayland has no «repaint "
      "now», but restarting the stream makes a buffer arrive. " + c("capture_wake()") + " repeats the current parameters at the "
      "negotiated size; on labwc it asks for the next frame whole (" + c("wlr_force_full()") + "). The child calls it only when "
      "a keyframe is owed and the capture returned zero, and at most every " + c("WAKEUP_MS") + " = 400 ms.") + \
    warn("on Mutter the renegotiation recreates the absolute input devices (the comment of " + c("capture.h") + " traces it to "
         + c("viewports-changed") + " and " + c("remove_viewport_devices()") + ", which does not go through " + c("drop_device()")
         + "). If a button is held at that moment it stays pressed inside Mutter and the desktop would take no other click. The "
         "child therefore does not wake the stream while " + c("input_pressed()") + " reports a key or button held; the price is "
         "that a client just attached may see a blank page until the user lets go. " + c("input.c") + " has a further healing "
         "for the doors the child does not control (" + rif("Input") + "). The chain was measured on Mutter 48.7 (Debian). In the source of "
         "Mutter 50.1 " + c("drop_device()") + " and " + c("handle_button()") + " are unchanged, but the cure was not measured again on "
         "Ubuntu: the bench that measured it is not in this tree.", "Wake-up and held buttons.") + \
    p("<b>When the compositor refuses the GPU path.</b> A machine without 3D acceleration has no DMA-BUF to offer, and the GPU "
      "proposal dies with «no more input formats». " + c("capture_format_refused()") + " recognises the facts (stream in error "
      "with no format ever agreed, or a format agreed and no frame ever delivered) and " + c("capture_start()") + " returns "
      + c("G_IO_ERROR_NOT_SUPPORTED") + " when it sees the refusal itself. " + c("falls_back_if_refused()") + " in the child then "
      "switches to memory, logs it, and never tries the GPU again in that process. The two paths are never offered together, "
      "because the compositor would choose and zero copy would be lost where it works. Silence (no frame in 5 s) does not "
      "trigger the fallback; only a refusal does. Since 17 Nov 2026 the package refuses a new installation on a machine with no "
      "DRM render node at all (" + rif("The package") + "), so this fallback is the safety net for a card that exists but gives "
      "no DMA-BUF.") + \
    p("<b>Closing the stage.</b> " + c("pw_stream_destroy()") + " when the stage is dismantled can wait for RealtimeKit for up to 25 s on a "
      "machine where " + c("rtkit-daemon") + " is installed but does not start: the real-time module of the two PipeWire contexts "
      "(" + c("capture.c") + ", " + c("sound.c") + ") stays in a D-Bus call. For that reason the child announces the end of a session "
      "before the stage is dismantled (" + rif("When the session ends before the stage is gone") + ").")

# ── 6 ───────────────────────────────────────────────────────────────────────
S6 = p("labwc has no PipeWire node. It offers " + c("zwlr_screencopy_manager_v1") + " (version 3), and every frame is a full "
       "round trip: " + c("capture_output") + ", " + c("buffer") + ", " + c("copy") + ", " + c("ready") + ". The frame rate is "
       "therefore REMOTIX's loop, not a property of the compositor.", lead=True) + \
    p("<b>Why a separate module.</b> " + c("capture.c") + " was built on the push direction and " + c("child.c") + " uses its "
      "interface in dozens of places; the comment of " + c("capture.h") + " counts thirty-five. Rewriting them for two directions "
      "would have put GNOME and KDE at risk to serve a new desktop. The shape copies the clipboard's precedent ("
      + c("clipboard_open()") + " and " + c("clipboard_open_kde()") + "): a second constructor, " + c("capture_start_wlr()")
      + ", and every public function of " + c("capture.c") + " hands over to " + c("wlroots.c") + " at the top when the capture "
      "is a wlroots one. Everything downstream (" + c("capture_take()") + ", " + c("capture_delivery()") + ", the counters) sees "
      "no difference.") + \
    table(["Topic", "What happens"], [
        ["Gate", "None: a bare client sees the screencopy global, and the only gate is the uid that owns the runtime folder."],
        ["Deprecation", "The protocol is deprecated upstream in favour of " + c("ext-image-copy-capture-v1") + "; the comments record that "
         "the labwc they were written against (0.8.3) does not expose that one. Ubuntu 26.04 has labwc 0.9.3; whether it exposes it is not "
         "verified, the rounds on XFCE and LXQt pass with " + c("zwlr_screencopy_manager_v1") + ". The module's interface names frames and sizes, not "
         "protocol messages, so a successor can be added beside it."],
        ["Opening", c("wlr_open()") + " connects (same socket search as KWin), checks the manager and chooses the output, but "
         "captures nothing: «the compositor is not there» and «the first frame does not come» stay two diagnoses."],
        ["Request", c("capture_output") + " with " + c("overlay_cursor = 1") + ": the pointer is drawn into the image. Frames are "
         "copied with " + c("copy_with_damage") + "; " + c("wlr_force_full()") + " makes the next copy a plain " + c("copy") + "."],
        ["Pending frame", "The child waits " + c("MOTION_WAIT_S") + " = 8 ms per turn and a round trip costs more. A wait that expires "
         "does not throw the frame away: the request stays alive and the next call resumes it."],
        ["Outcomes", c("WLR_FRAME_TAKEN") + ", " + c("WLR_FRAME_FAILED") + " (the compositor sent " + c("failed") + "), "
         + c("WLR_FRAME_EXPIRED") + " (could not look), " + c("WLR_FRAME_BROKEN") + " (the connection fell): «the compositor said "
         "no» is never confused with «I could not ask»."],
        ["Pixel order", "The " + c("buffer") + " event speaks " + c("wl_shm") + " numbering (0 and 1 special); " + c("shm_a_drm()")
         + " translates it. The comments record labwc offering only " + c("XBGR8888") + " (R G B x) in memory, so " + c("child.c")
         + " tells the encoder " + c("CODIFICATORE_PIXEL_RGBX") + ", and " + c("XRGB8888") + " (B G R x) on the GPU path. "
         + c("widen_24()") + " widens a 24-bit memory format to 32 bits."],
        ["Orientation", "The " + c("flags") + " event can say the rows are bottom-up (" + c("y_inverted") + "); ignoring it would give an "
         "upside-down image that looks like an encoder fault."],
        ["Size", "A headless labwc output is born at a fixed size that REMOTIX has to change. " + c("wlr_ask_size()") + " uses "
         + c("zwlr_output_manager_v1") + " and returns " + c("WLR_SIZE_REQUESTED") + ", " + c("WLR_SIZE_UNCHANGED") + ", "
         + c("WLR_SIZE_REFUSED") + " (" + c("failed") + "), " + c("WLR_SIZE_CANCELLED") + " (" + c("cancelled") + ": stale serial, "
         "retry) or " + c("WLR_SIZE_IMPOSSIBLE") + ". Other heads are re-confirmed as they are, because with two outputs a "
         "configuration that names one dies with " + c("unconfigured_head") + "."],
    ], "«TAB» — The wlroots capture, " + c("wlroots.c")) + \
    p("The environment in which this compositor is born is set by " + c("session.c") + ": " + c("WLR_BACKENDS=headless")
      + " (no seat and no libseat), " + c("WLR_LIBINPUT_NO_DEVICES=1") + ", " + c("LABWC_UPDATE_ACTIVATION_ENV=1") + " (without it "
      "labwc does not propagate " + c("WAYLAND_DISPLAY") + " to the bus), and "
      + c("WLR_RENDER_DRM_DEVICE") + " with the node chosen by " + c("card_pick_desktop()") + ", or " + c("WLR_RENDERER=pixman")
      + " as a declared fallback when no card can create the output buffer (" + rif("Video encoding") + ").")

# ── 7 ───────────────────────────────────────────────────────────────────────
SLABS = fig(
    box(40, 40, 180, 60, "FREE", "may be named in a copy", "green")
    + box(360, 40, 180, 60, "IN FLIGHT", "named in the current copy", "blue")
    + box(680, 40, 180, 60, "IN HAND", "delivered to the encoder", "navy")
    + arrow(222, 70, 358, 70, label="capture_output + copy")
    + arrow(542, 70, 678, 70, label="ready + GPU fence")
    + path([(770, 102), (770, 150), (130, 150), (130, 102)], label="wlr_release() after the encoder returns", lx=450, ly=142)
    + path([(450, 102), (450, 186), (60, 186), (60, 102)], "#d97706", True,
           label="failed or connection lost: the slab is dirty, rebuilt", lx=300, ly=204),
    900, 216, "«FIG» — The three states of a slab; a slab in hand is never named in a copy")

S7 = p("On labwc the zero-copy path is a <i>copy</i> into a DMA-BUF that REMOTIX owns. A «slab» is a GBM buffer allocated on the "
       "compositor's render node, its DMA-BUF descriptor and the " + c("wl_buffer") + " that names it. " + c("wlr_ask_card()")
       + " enables the path and says no in writing if it cannot, leaving memory as a declared fallback. The module chose it over "
       + c("zwlr_export_dmabuf_manager_v1") + " because the exported buffers belong to the compositor's swap chain, are reused every "
       "turn and are always marked transient, with no lever at all on reuse; a buffer of REMOTIX's own costs one blit on the GPU "
       "and one dependency, " + c("gbm") + ".", lead=True) + SLABS + \
    ul(["<b>Three slabs</b> (" + c("WLR_SLABS") + "): one in hand, one in flight, one as insurance. If all are in hand the frame "
        "stops and says so; a slab in hand is never recycled, and " + c("wlr_release()") + " is called from "
        + c("capture_stopped_free()") + ", after the encoder has finished reading.",
        "<b>Linear modifier.</b> The " + c("linux_dmabuf") + " event carries format and size, not modifiers, so slabs are LINEAR. "
        "The exception is a card whose GBM refuses linear rendering buffers: the slab is then allocated with one of the modifiers "
        "the Vulkan encoder imports (" + c("vulkanvideo_modifiers()") + ").",
        "<b>Exact format.</b> The slab is allocated in exactly the format and size of the " + c("linux_dmabuf") + " event; anything "
        "else is " + c("invalid buffer") + ", a protocol error that kills the connection.",
        "<b>Synchronisation.</b> The comments record that wlroots ends the blit with " + c("glFlush()") + " and sends " + c("ready")
        + " at once, and that labwc offers no explicit-sync protocol. After " + c("ready") + " REMOTIX extracts the fence from the "
        "DMA-BUF (" + c("DMA_BUF_IOCTL_EXPORT_SYNC_FILE") + " with " + c("DMA_BUF_SYNC_READ") + ") and polls it; the wait is "
        + c("gpu_wait_us") + ". Without the ioctl it is said once and implicit synchronisation is trusted.",
        "<b>Generation.</b> Every slab that is born or dies changes the generation, for the same descriptor-reuse reason as on PipeWire.",
        "<b>Switching off.</b> " + c("WLR_CARD_FAILED_MAX") + " = 3 consecutive " + c("failed") + " on the GPU path turn it off, and the "
        "log says so; the first slab birth may take up to " + c("WLR_SLAB_BIRTH_S") + " = 1 s."]) + \
    warn("when the encoder is Vulkan, " + c("slabs_per_route()") + " calls " + c("wlr_slabs_at_max_canvas()") + " and the slabs are "
         "born at " + c("WLR_SLAB_W") + " × " + c("WLR_SLAB_H") + " = 4096×2304 (the largest canvas, " + c("RCP_CANVAS_MAX_W") + " ×"
         " " + c("RCP_CANVAS_MAX_H") + "), and a resize changes only the " + c("wl_buffer") + ", never the GBM object. The comment of "
         + c("wlroots.c") + " explains why: GBM (radeonsi) and Vulkan (RADV) in the same process share one " + c("amdgpu_device") + ", "
         "and freeing a GBM buffer right before creating the Vulkan encoder at the new size is recorded as a page fault, "
         + c("VK_ERROR_DEVICE_LOST") + " and a card reset (10 faults in 14 runs with slabs freed on resize, 0 in 5 with slabs kept, "
         "on an AMD card; measured on an earlier build, never re-measured on Ubuntu). The cost is 3 × 4096 × 2304 × 4 = about 113 MB "
         "per session even at 1080p, so it applies only to the Vulkan route. With VA-API the slabs keep the canvas size. Which route a "
         "Radeon takes on Ubuntu 26.04 is in " + rif("Choosing the GPU route") + ".",
         "Slabs and the AMD GPU hang.")

# ── 8 ───────────────────────────────────────────────────────────────────────
STRADE = fig(
    zone(20, 12, 860, 112, "GPU path (default, ZERO_COPY = 1)")
    + box(40, 46, 190, 60, "Compositor", "frame already on the GPU", "navy")
    + box(265, 46, 190, 60, "DMA-BUF", "retained or slab in hand", "blue")
    + box(490, 46, 170, 60, "Import (cached)", "VA surface / VkImage", "blue")
    + box(690, 46, 170, 60, "Convert + encode", "VPP or shader, GPU", "light")
    + arrow(232, 76, 263, 76) + arrow(457, 76, 488, 76) + arrow(662, 76, 688, 76)
    + zone(20, 140, 860, 112, "Memory path (declared fallback)")
    + box(40, 174, 190, 60, "Compositor", "MemFd / wl_shm", "dark")
    + box(265, 174, 190, 60, "memcpy", "in the RT callback", "grey")
    + box(490, 174, 170, 60, "BT.709 in CPU", "colors709.c (VA-API)", "grey")
    + box(690, 174, 170, 60, "Upload + encode", "planes to the GPU", "light")
    + arrow(232, 204, 263, 204) + arrow(457, 204, 488, 204) + arrow(662, 204, 688, 204),
    900, 264, "«FIG» — The two paths of a frame; on Vulkan the memory path uploads RGB and the same shader converts")

S8 = p("«Zero copy» means the frame never leaves the GPU between the compositor and the encoder. It is the default: "
       + c("ZERO_COPY") + " is 1 in " + c("child.c") + ", and a compile-time " + c("-DZERO_COPY=0") + " exists only to rebuild the "
       "«before» for A/B comparisons. It is not zero work: the RGB to YUV conversion still happens, on the GPU.",
       lead=True) + STRADE + \
    table(["The GPU path is abandoned when…", "Detected by", "Consequence"], [
        ["The compositor has no DMA-BUF to offer", c("capture_format_refused()") + ", " + c("G_IO_ERROR_NOT_SUPPORTED"),
         "Memory for the whole process (" + c("card_never_again") + ")"],
        ["The measured stride is not a multiple of 64 bytes", c("encoder_stride_importable()") + " on the first frame",
         "Memory for this canvas only (" + c("card_denied_w") + ", " + c("card_denied_h") + "); the GPU path is retried on the next canvas"],
        ["The encoder is not on the GPU", c("codificatore_in_hardware()"), "Memory for the whole process (a guard: the encoder is always on the card)"],
        ["Three " + c("failed") + " in a row on labwc slabs", c("wlroots.c"), "Memory, logged"],
    ], "«TAB» — When the frame goes through memory") + \
    p("<b>The 64-byte stride.</b> " + c("CARD_ALIGNMENT") + " in " + c("encoder.c") + " is 64 bytes. The comments record that the Intel "
      "iHD driver, importing a DMA-BUF whose stride is not a multiple of 64, reads rows at its own pitch and the desktop comes out "
      "blurred and slanted while the timing looks perfect, with no error. The producer makes the stride equal to " + c("width × 4")
      + ", so the code refuses the GPU path for such a canvas and declares it, rather than sending a wrong image.") + \
    p("<b>Remounting only the capture.</b> Switching path does not tear down the stage. " + c("remount_only_capture()") + " stops and "
      "reopens only the " + c("Capture") + " and its cursor hook, keeping the input channel, the clipboard and the "
      + c("RemoteDesktop") + " session; the comments record a crash inside " + c("ei_disconnect()") + " after a full teardown shortly "
      "after the EIS channel was opened. On labwc the capture <i>is</i> the source, so remounting means " + c("capture_stop()") + " and "
      + c("capture_start_wlr()") + ".") + \
    note("the frame rate is one number, " + c("MOTION_FPS") + " = 60, used both for the capture maximum and for the encoder. The "
         "child waits " + c("MOTION_WAIT_S") + " = 8 ms per turn, so that on a still desktop a click does not wait in the socket "
         "for a long poll.", "One frame rate, short waits.")

# ── 9 ───────────────────────────────────────────────────────────────────────
S9 = p("The pointer is drawn by the page, not baked into the video: the image stays clean (two pointers are worse than one) and "
       "the shape travels as a side channel, the " + c("CURSOR_SHAPE") + " message of RCP/1. The capture's only addition to its "
       "interface is the registration of the receiver (the seam is described at the end of " + c("capture.h") + "); "
       + c("cursor.c") + " sits between the capture and the wire. The shape is delivered from the capture, on the real-time "
       "thread for the PipeWire desktops.", lead=True) + \
    table(["State", "Metadata", "What is sent"], [
        ["Not received", "No cursor metadata in the buffer", "Nothing; " + c("capture.c") + " counts it (" + c("cursor_absent") + ") and the page keeps its own pointer"],
        ["Hidden", c("id = 0") + ", or a bitmap with no visible pixel", c("CURSOR_SHAPE") + " 0×0 with hotspot 0,0, unless "
         + c("cursor_never_hide()") + " is on (KDE)"],
        ["Unchanged", c("bitmap_offset = 0") + " (the metadata comes with every buffer)", "Nothing; the series number grows only on a real change"],
        ["Changed", "A new bitmap", "The shape, converted from premultiplied RGBA to premultiplied BGRA, cropped to " + c("CURSOR_MAX_SIDE")
         + " = 256 and the crop logged"],
    ], "«TAB» — The four cursor states that cursor.c separates") + \
    p("After a hidden period Mutter sends «unchanged» when the pointer comes back, so " + c("cursor.c") + " keeps the last visible "
      "shape and re-sends it; otherwise the pointer would stay invisible with no error. A cursor larger than 256 would make the "
      "receiver close the session with a protocol error, which is why the limit is enforced on this side. A malformed metadata "
      "block is declared in the log (" + c("malformed_cursors") + ") and nothing is sent.") + \
    table(["Desktop", "Where the shape comes from"], [
        ["GNOME", "Mutter's metadata, a real bitmap from the theme in use."],
        ["KDE Plasma", "KWin's metadata (mode 4). KWin also paints the pointer into the image (software cursor), so the session runs "
         "with REMOTIX's encoded theme: the metadata is a single opaque pixel whose colour names the shape, and " + c("cursor.c")
         + " replaces it with the real image (" + c("shape_from_pixel()") + ", " + c("shape_image()") + ")."],
        ["XFCE, LXQt", "No cursor channel in screencopy. After injected pointer gestures the child calls " + c("capture_probe_pointer()")
         + "; a 3×3 region capture around the hotspot reads the encoded pixel, and the shape is delivered from " + c("capture_take()")
         + " on the child's thread."],
    ], "«TAB» — The pointer shape on each desktop")

S10 = p("KWin and labwc draw the pointer into the captured image, so their sessions run with a cursor theme of REMOTIX's own, "
        + c("SHAPE_THEME") + " = " + c("remotix-invisible") + ". Each shape of that theme is a 1×1 image, <b>opaque</b> and of a colour "
        "that is its alone. The server writes the theme before the desktop starts (" + c("shape_theme_write()") + " is called from "
        + c("session.c") + "); the child reads the colour and looks up the real image in a real theme on disk. The design is an "
        "<b>encoded theme plus a dictionary</b> (" + c("shape.h") + ", " + c("shape.c") + ").", lead=True) + \
    table(["Item", "Value"], [
        ["Theme name", c("SHAPE_THEME") + " = " + c("remotix-invisible") + ", the same as always, so the sessions' " + c("XCURSOR_THEME") + " does not change"],
        ["Where", c("<runtime>/remotix/icons/remotix-invisible/") + " written by " + c("shape_theme_write()") + "; "
         + c("<runtime>/remotix/icons") + " goes into " + c("XCURSOR_PATH")],
        ["Shapes", c("SHAPE_COUNT") + " = 78. The index is the code: new names are appended, never inserted"],
        ["Colour of shape i", "red = 0x40 + i, green = 0xA5 xor i, blue = (7·i mod 256) xor 0x5A, alpha 0xFF (" + c("shape.c") + "). "
         "Red alone distinguishes the shapes; green and blue are the check. The lookup is exact to the byte"],
        ["Real themes", c("REAL_THEMES") + " = " + c("Adwaita") + ", then " + c("breeze_cursors") + "; name, then aliases, then the arrow. "
         "If neither theme is on the machine " + c("shape_image()") + " fails once in the log and the client keeps its own arrow"],
        ["Nominal size", c("SHAPE_SIZE") + " = 24"],
        ["Parser", "Xcursor files read by REMOTIX itself (no " + c("libXcursor") + "); files over " + c("FILE_MAX") + " = 8 MiB are refused"],
    ], "«TAB» — The encoded cursor theme") + \
    p("<b>The labwc probe.</b> " + c("wlr_probe_pointer()") + " runs a " + c("capture_output_region") + " of 3×3 pixels around the "
      "hotspot into a small " + c("wl_shm") + " buffer; the centre is checked, then the neighbours. Only one probe is in flight, "
      "coalescing to the last position; it is a plain " + c("copy") + ", never with damage; and a <i>tail probe</i> "
      + c("PROBE_TAIL_US") + " = 120 ms after the hand stops catches the shape change a client makes after the " + c("enter")
      + " event. " + c("MIN_PROBE_US") + " is 0: probes are not thinned.") + \
    warn("the compositor now paints one coloured pixel under the hotspot into the image. The browser's pointer covers it and the "
         "encoder smears it; the header of " + c("shape.h") + " marks «never visible» as not settled until someone looks, and nobody has "
         "looked by eye. The " + c("pointer-shape-*") + " checks pass on the four desktops in the Ubuntu rounds. Which real theme is "
         "found on Xubuntu and Lubuntu depends on the themes installed (" + c("REAL_THEMES") + " lists Adwaita then breeze_cursors): not verified.", "The declared price.")

# ── 10 ──────────────────────────────────────────────────────────────────────
S11 = p("The constants of the capture, where they live.", lead=True) + \
    table(["Constant", "Value", "File", "Role"], [
        [c("MOTION_FPS"), "60", c("child.c"), "Capture maximum and encoder rate"],
        [c("MOTION_WAIT_S"), "0.008 s", c("child.c"), "Wait per loop turn"],
        [c("WAKEUP_MS"), "400 ms", c("child.c"), "Minimum interval between stream wake-ups"],
        [c("ZERO_COPY"), "1", c("child.c"), "GPU path by default"],
        [c("WAIT_LATCH_MS"), "10000 ms", c("capture.c"), "Wait for the PipeWire stream to attach, per attempt"],
        [c("PIXEL_SCAN_EVERY_MS"), "500 ms", c("capture.c"), "Diagnostic pixel scan cadence"],
        [c("MAX_REGIONS"), "16", c("capture.c"), "Damage regions carried per frame"],
        [c("WAIT_CALL_MS") + " / " + c("WAIT_NODE_MS"), "15000 / 10000 ms", c("mutter.c"), "D-Bus call and node announcement"],
        [c("WAIT_NODE_MS"), "5000 ms", c("kwin.c"), "Node announcement from KWin"],
        [c("POINTER_METADATA"), "4", c("kwin.c"), "Cursor as metadata"],
        [c("HOST_MHZ"), "240000", c("kwin.c"), "Refresh of the labwc that hosts KWin"],
        [c("TICKER_MS"), "16 ms", c("kwin.c"), "Damage interval of the 1×1 ticker surface"],
        [c("HOST_BIRTH_MS"), "10000 ms", c("kwin.c"), "Wait for the socket of KWin's labwc at session birth"],
        [c("LOST_QUIET_MS"), "200 ms", c("capture.c"), "Silence after which a lost frame is asked again"],
        [c("LOST_POKES_MAX"), "10", c("capture.c"), "Pokes in a row without a picture before it stops"],
        [c("SEQ_WINDOW"), "600", c("capture.c"), "Buffers in the window of the safety switch (switch off above half holes)"],
        [c("REMOTIX_LABWC"), c("/usr/libexec/remotix/labwc"), c("Makefile"), "Compile-time path of the labwc that hosts KWin"],
        [c("WLR_SLABS"), "3", c("wlroots.c"), "Slabs"],
        [c("WLR_CARD_FAILED_MAX"), "3", c("wlroots.c"), "Consecutive failures before the GPU path is switched off"],
        [c("WLR_SLAB_W") + " × " + c("WLR_SLAB_H"), "4096 × 2304", c("wlroots.c"), "Slab size with Vulkan encoding"],
        [c("PROBE_TAIL_US"), "120 ms", c("wlroots.c"), "Tail probe after the last pointer gesture"],
        [c("CURSOR_MAX_SIDE"), "256", c("cursor.h"), "Wire limit of " + c("CURSOR_SHAPE")],
        [c("SHAPE_COUNT") + " / " + c("SHAPE_SIZE"), "78 / 24", c("shape.h"), "Encoded theme"],
    ], "«TAB» — Capture constants") + \
    p("Every capture line in the log carries the area " + c("capture") + ", also those written by " + c("kwin.c") + ", " + c("mutter.c")
      + " and " + c("wlroots.c") + ". The line written when the stage is mounted names the route (CARD or MEMORY), because the timings "
      "of the two are not the same quantity (" + rif("Logging and diagnostics") + ").") + \
    h4("What was verified, and what was not") + \
    ul(["The round of 26-27 Nov 2026 ran " + c("prove/all.sh") + " on the four desktops, each in its own virtual machine with the Radeon handed over (" + c("RX_BANCO=vm") + "), with Chrome and Firefox: GNOME 125 PASS and one known FAIL, KDE, XFCE and LXQt 126 PASS. "
        "The cures described in this chapter (the early farewell of the session, the ScreenSaver sidecar, the lost-frame cure, the GNOME scale cure) were made in the rounds of 18 and 19 Nov 2026, before 1.0.1 (" + c("docs/STORIA-ubuntu-26.04.md") + "). The picture, a moving counter, bursts "
        "that stop and the frame rate are measured by " + c("prove/check-media.py") + "; the capture is exercised through them but no "
        "check isolates the capture alone (" + rif("Testing") + ").",
        "The owner's hand tests: the four virtual machines and the four live images 26.04.1 on a real machine (27 Nov 2026) found everything regular.",
        "Not verified on Ubuntu: the nested KWin without our labwc (" + c("--virtual") + " fallback) beyond a first check on the Kubuntu "
        "box; the shape probe and the encoded theme by eye; NVIDIA with GNOME on this tree (the modifier path of " + c("capture_modifiers_card()") + "; measured on Ubuntu 26.04 on 6 Oct 2026 with an earlier version of the code); a canvas of 4096×2304 end to end (the test "
        "browser's decoder stops at 3840×2160); the lost-frame cure on a real machine beyond the hand tests."])

CHAPTER = ("Screen capture", [
    ("Capture at a glance: one contract, three compositor families", S1),
    ("The capture contract", S2),
    ("GNOME: the Mutter D-Bus sequence", S3),
    ("KDE: the KWin screencast protocol and the nested KWin", S4),
    ("The lost frame (KWin)", S4B),
    ("PipeWire negotiation, resize and wake-up", S5),
    ("XFCE and LXQt: wlroots screencopy", S6),
    ("Slabs: zero copy on labwc", S7),
    ("Zero copy and the memory fallback", S8),
    ("The cursor channel", S9),
    ("The encoded cursor theme", S10),
    ("Capture constants and what was verified", S11),
])
