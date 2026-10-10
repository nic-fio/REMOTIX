from build import arrow, box, c, fig, h4, note, p, path, rif, table, text, tip, ul, warn, zone

# ── 6.1 ─────────────────────────────────────────────────────────────────────
FAMIGLIE = fig(
    zone(20, 12, 860, 118, "The compositor of the user's session")
    + box(40, 46, 250, 66, "Mutter (GNOME)", "D-Bus ScreenCast + RemoteDesktop", "navy")
    + box(325, 46, 250, 66, "KWin (KDE Plasma)", "zkde_screencast_unstable_v1", "navy")
    + box(610, 46, 250, 66, "labwc (XFCE, LXQt)", "zwlr_screencopy_manager_v1", "navy")
    + box(40, 170, 250, 56, "mutter.c", "the D-Bus sequence", "blue")
    + box(325, 170, 250, 56, "kwin.c", "the Wayland request", "blue")
    + box(610, 170, 250, 56, "wlroots.c", "frames pulled one by one", "blue")
    + box(40, 262, 535, 56, "PipeWire node", "frames are pushed: cattura_avvia(node)", "dark")
    + box(610, 262, 250, 56, "No PipeWire", "cattura_avvia_wlr()", "dark")
    + box(160, 356, 580, 60, "cattura.c — one contract", "cattura_prendi() · cattura_fermo_libera() · counters", "light")
    + arrow(165, 114, 165, 168) + arrow(450, 114, 450, 168) + arrow(735, 114, 735, 168)
    + arrow(165, 228, 165, 260) + arrow(450, 228, 450, 260) + arrow(735, 228, 735, 260)
    + arrow(307, 320, 380, 354) + arrow(735, 320, 640, 354)
    + text(450, 448, "figlio.c reads the same interface on all four desktops", 11, "#475569"),
    900, 460, "«FIG» — Three compositor families, two directions (push and pull), one capture contract")

S1 = p("REMOTIX does not grab the physical screen: every session has its own virtual output, and the "
       "capture reads that output from the compositor that draws it. There are three compositor families "
       "behind the four desktops, and they deliver frames in two opposite directions. GNOME and KDE "
       "<i>push</i> frames through a PipeWire node; labwc (the compositor REMOTIX runs under XFCE and LXQt) "
       "has no node at all, and frames are <i>pulled</i> one by one. All three end up behind one interface, "
       + c("cattura.h") + ", which the per-user child process (" + c("figlio.c") + ") uses in the same way "
       "on every desktop.", lead=True) + FAMIGLIE + \
    table(["", "GNOME (Mutter)", "KDE Plasma (KWin)", "XFCE and LXQt (labwc)"], [
        ["Module that opens the source", c("mutter.c") + " — " + c("mutter_apri()"),
         c("kwin.c") + " — " + c("kwin_apri()"), c("wlroots.c") + " — " + c("wlr_apri()")],
        ["How frames arrive", "Pushed, PipeWire node from " + c("RecordVirtual"),
         "Pushed, PipeWire node from " + c("stream_output"), "Pulled: " + c("capture_output") + " → "
         + c("copy") + " → " + c("ready") + " per frame"],
        ["Virtual output", "Created by " + c("RecordVirtual") + " at every stage assembly (" + c("Meta-1")
         + ", product name «Virtual remote monitor»)", c("Virtual-0") + ", created by " + c("kwin_wayland --virtual --width W --height H")
         + " when the session is born", "Headless output of labwc (" + c("HEADLESS-1") + "), born 1280×720"],
        ["Access gate", "None beyond the user's own D-Bus session (direct compositor interfaces, no portal)",
         "A " + c(".desktop") + " file that lists the protocol in " + c("X-KDE-Wayland-Interfaces"),
         "None: the only gate is the uid (" + c("/run/user/<uid>") + " is " + c("drwx------") + ")"],
        ["Resize while live", "Yes: " + c("pw_stream_update_params()"), "No: the output size is fixed by the "
         "command line; the page rescales", "Yes: " + c("zwlr_output_manager_v1") + " changes the output"],
        ["Zero copy (DMA-BUF)", "Yes, negotiated with modifiers", "Yes, negotiated with modifiers",
         "Yes, into GBM buffers owned by REMOTIX (“slabs”)"],
        ["Pointer shape", "Mutter cursor metadata (" + c("cursor-mode=2") + ")",
         "KWin cursor metadata (mode 4) carrying the encoded theme pixel",
         "Pointer drawn into the image; a 3×3 probe reads the encoded theme pixel"],
    ], "«TAB» — The capture, desktop by desktop") + \
    p("Which family is in use is decided once per process by " + c("sessione_desktop()") + " (see "
      + rif("The four desktops") + "); there is no per-compositor switch inside the capture. Where a "
      "compositor cannot do something (KWin cannot resize its virtual output), the behaviour is the same "
      "for everyone that cannot: the stream keeps its size and the page rescales.")

# ── 6.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The capture has one job, written at the top of " + c("cattura.h") + ": deliver a frame with the "
       "<i>declared</i> buffer type, never a deduced one. Three rules from REMOTIX v1 survived the rewrite, "
       "and each one exists because breaking it produces no error at all.", lead=True) + \
    table(["Rule", "What the code does", "Why"], [
        ["The stride is read, never computed", "The stride comes from the buffer chunk. A frame with "
         + c("stride == 0") + " is discarded and counted (" + c("stride_zero") + ") instead of being given "
         + c("width × 4") + ".",
         "A producer may pad rows. A wrong stride gives a slanted image that looks almost right. Measured on "
         "12 Aug 2026 at 1920×1080: stride 7680, exactly " + c("width × 4") + " — which is why the rule must "
         "be written down before the day it stops matching."],
        ["The buffer type is asked in two places", "DMA-BUF is requested both in the " + c("modifier")
         + " field of the format (" + c("MANDATORY | DONT_FIXATE") + ") and with the " + c("SPA_DATA_DmaBuf")
         + " bit in " + c("SPA_PARAM_Buffers") + ".", "With only one of the two the negotiation still succeeds "
         "and buffers keep arriving in memory: no error, no log line, no zero copy (measured 6 Aug 2026)."],
        ["The frame rate is declared as zero", c("framerate = 0/1") + " plus " + c("maxFramerate")
         + " up to " + c("MOVIMENTO_FPS") + " (60).", "“Send a frame when something changes.” On a still "
         "desktop nothing arrives, and that is a result, not a fault."],
    ], "«TAB» — The three rules of the capture") + \
    p("The negotiated facts are exposed in " + c("CatturaConsegna") + " (read with " + c("cattura_consegna()")
      + "), four groups that the code downstream reads instead of recomputing:") + \
    ul(["<b>buffer type</b> — requested (" + c("strada_chiesta") + ", " + c("buffer_chiesto") + ") and "
        "declared by the producer (" + c("buffer_dichiarato") + "), in separate fields: what arrives is the "
        "answer to the question REMOTIX asked, not a discovery about the compositor;",
        "<b>bits per channel</b> — from the negotiated format; 0 means unknown and is written as 0;",
        "<b>geometry</b> — size, the stride read from the chunk (" + c("stride_letto")
        + " says whether it is a fact or still empty), the DRM modifier;",
        "<b>colour</b> — range, matrix, transfer and primaries as the producer declares them, “not declared” "
        "included; plus what REMOTIX measures itself on the pixels (min/max per channel, black, uniform)."]) + \
    p("The pixel measurement (" + c("misura_i_pixel()") + ") is diagnostic only. It runs on the first frame and "
      "then at most every " + c("MISURA_PIXEL_OGNI_MS") + " = 500 ms, because on 22 Aug 2026 it cost 5.34 ms of a "
      "21.61 ms capture-to-bytes path (25 %) on the test server at 1920×1080, to fill one log line. "
      + c("pixel_misurati") + " sits beside the results so that “not black” and “not looked at” cannot be "
      "confused. Sampling one pixel in eight (0.10 ms) was measured and rejected: a frame black except for one "
      "region would be reported as black.") + \
    table(["Outcome of " + c("cattura_prendi()"), "Meaning", "What the caller does"], [
        [c("CATTURA_PRESA_FATTA"), "A frame was copied into memory", "Encode from " + c("pixel")],
        [c("CATTURA_PRESA_PIXEL_ALTROVE"), "A frame was delivered on the GPU path: " + c("pixel")
         + " is NULL, " + c("fd") + "/" + c("offset") + "/" + c("stride") + "/" + c("modificatore")
         + " describe a DMA-BUF that is <b>retained</b>", "Encode from the descriptor, then "
         + c("cattura_fermo_libera()")],
        [c("CATTURA_PRESA_ZERO"), "The stream was active for the whole wait and nothing arrived (still desktop)",
         "Nothing; it is a legitimate zero"],
        [c("CATTURA_PRESA_GUASTO"), "The stream was never active, or has died", "Report, remount the stage"],
    ], "«TAB» — Zero and failure are different outcomes") + \
    warn("the PipeWire callbacks run on PipeWire's own real-time thread (" + c("pw_thread_loop") + "). Nothing "
         "may wait inside them, " + c("cattura_ferma()") + " must not be called from the end callback, and the "
         "pixels live only for the duration of the callback: the copy into REMOTIX's buffer is made there, "
         "and frames that arrive while nobody is waiting are only counted, not copied.",
         "Real-time thread.") + \
    p(c("CatturaFermo") + " also carries the timing of the part of the path that precedes the encoder, in "
      "microseconds of " + c("CLOCK_MONOTONIC") + " (the same clock as " + c("figlio.c") + " and "
      + c("codificatore.c") + "): " + c("us_arrivo") + " (when the frame was parked), " + c("us_copia")
      + " (the " + c("memcpy") + " in the callback), " + c("us_allocazione") + " (0 when the buffer was reused), "
      + c("us_nel_posto") + " (how long the frame waited for a taker) and " + c("us_misura") + ". They were "
      "added in phase 8 because about 16 ms of a 30.37 ms capture-to-first-byte path had no owner.") + \
    p("The damage regions (" + c("SPA_META_VideoDamage") + ") are information about how much changed, not a "
      "condition for reading the buffer. v1 believed Mutter repainted only the damaged part of recycled "
      "buffers; on 12 Aug 2026 (Mutter 48.7, memory path, 410 frames) damage was partial on every frame and "
      "the SMPTE bars were whole in every one. The buffer is always complete.")

# ── 6.3 ─────────────────────────────────────────────────────────────────────
SEQ = fig(
    "".join(text(x, 40, t, 12, "#003a90", "700") for x, t in
            [(110, "mutter.c"), (330, "RemoteDesktop"), (560, "ScreenCast"), (790, "PipeWire")])
    + "".join(f'<line x1="{x}" y1="50" x2="{x}" y2="372" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 4"/>'
              for x in (110, 330, 560, 790))
    + arrow(115, 72, 325, 72, label="1  CreateSession → read SessionId")
    + arrow(325, 104, 115, 104, "#475569", True, label="ConnectToEIS (input channel)")
    + arrow(115, 136, 555, 136, label="2  CreateSession(remote-desktop-session-id)", lx=330)
    + arrow(115, 168, 325, 168, label="3  Session.Start — only now")
    + arrow(115, 200, 555, 200, label="4  RecordVirtual(cursor-mode=2, is-platform)", lx=330)
    + arrow(115, 232, 555, 232, "#475569", True, label="subscribe PipeWireStreamAdded first", lx=330)
    + arrow(115, 264, 555, 264, label="5  Stream.Start", lx=330)
    + arrow(555, 296, 115, 296, "#475569", True, label="signal: PipeWire node id", lx=330)
    + arrow(115, 328, 785, 328, label="cattura_avvia(node): format proposal, buffers, metadata", lx=450)
    + arrow(785, 360, 115, 360, "#475569", True, label="streaming: the virtual monitor now exists", lx=450),
    900, 384, "«FIG» — The obligatory Mutter sequence; any permutation fails with a different error")

S3 = p("On GNOME REMOTIX talks to Mutter's direct D-Bus interfaces, " + c("org.gnome.Mutter.RemoteDesktop")
       + " and " + c("org.gnome.Mutter.ScreenCast") + ", not to " + c("xdg-desktop-portal") + ": the portal "
       "asks permission of a user sitting at the screen, and a headless session has nobody there. It is also "
       "the path gnome-remote-desktop uses.", lead=True) + SEQ + \
    p("The order admits no permutation, and each wrong order is punished with a different message that never "
      "says “wrong order”: starting the control session before step 2 gives “Remote desktop session already "
      "started”; starting the capture with " + c("Session.Start") + " gives “Must be started from remote "
      "desktop session”. Closing follows the same logic in reverse: " + c("mutter_chiudi()") + " stops the "
      "<i>control</i> session and the capture follows it. The PipeWire node is announced by a signal emitted "
      "<i>during</i> " + c("Stream.Start") + ", so " + c("mutter.c") + " subscribes before calling it (without a "
      "sender filter, to avoid the window in which GDBus resolves the owner of a name).") + \
    table(["Detail", "Value in the code", "Why"], [
        [c("cursor-mode"), c("CURSORE_METADATO") + " = 2", "The pointer is removed from the pixels and sent as "
         "metadata; the page draws it (" + rif("The cursor channel") + ")."],
        [c("is-platform"), "true", "The virtual monitor is configured like a real screen, as the reference "
         "implementation does."],
        [c("mapping-id"), "A random UUID is sent", "Measured 14 Aug 2026: Mutter ignores it. The real key is the "
         "UUID Mutter publishes in the stream's " + c("Parameters") + ", read by " + c("mutter_mapping_id_pubblicato()")
         + " for the input region."],
        ["D-Bus call timeout", c("ATTESA_CHIAMATA_MS") + " = 15000", ""],
        ["Wait for the node", c("ATTESA_NODO_MS") + " = 10000", "The node arrives as a signal; without a ceiling "
         "a lost signal would wait forever."],
    ], "«TAB» — What RecordVirtual is asked") + \
    p("The virtual monitor is mounted by the program at every stage assembly, never by configuration. In v1 "
      "the GNOME branch lost width and height and the monitor lived in a provisioning script; on 12 Aug 2026 "
      "a session ran for two days alive, complete and black. Putting the protection in the program means "
      "removing it takes intent.") + \
    p("Our monitor is identified by <b>name</b>, never by index or size. On the test server there were two "
      "virtual monitors, " + c("Meta-0") + " («MetaVirtualMonitor», the session's) and " + c("Meta-1")
      + " («Virtual remote monitor», ours), both 1920×1080@60. " + c("mutter_monitor_cerca()") + " compares "
      "the connectors before and after " + c("RecordVirtual") + " and the product name; if the two do not "
      "agree on exactly one new monitor, the answer is “unknown”, not a guess. It must be called once the "
      "stream is active: measured, the monitor does not exist after " + c("RecordVirtual") + ", nor three "
      "seconds after " + c("Stream.Start") + " — Mutter creates it when a consumer actually starts reading.") + \
    warn("with " + c("org.gnome.desktop.interface scaling-factor = 2") + " the stream keeps the requested pixels "
         "but the logical monitor gets scale 2.0, and its layout is the coordinate space of input: the pointer "
         "lands elsewhere with no log line. " + c("mutter_scala_nostra()") + " reads the scale of <i>our</i> "
         "monitor (a HiDPI laptop panel is not a defect); if it is not 1.0 the child refuses the stage and logs "
         "the one-line cure. A scale that cannot be read (−1) is declared and the session proceeds.",
         "Scale guard.") + \
    p("The bus connection belongs to the " + c("MutterSessione") + " and is lent out by " + c("mutter_bus()")
      + ": the clipboard uses the same " + c("RemoteDesktop") + " session (a second connection would be a "
      "second sender that Mutter does not recognise as the owner). The input channel opened here with "
      + c("ConnectToEIS") + " and its recovery " + c("mutter_eis_riattacca()") + " are described in "
      + rif("Input") + ".")

# ── 6.4 ─────────────────────────────────────────────────────────────────────
S4 = p("On Plasma the capture is a Wayland request to KWin: the private protocol "
       + c("zkde_screencast_unstable_v1") + " (version 5 on KWin 6.3.6), asked for the output "
       + c("Virtual-0") + ", answers with the id of a PipeWire node. From the node on, the path is the GNOME one: "
       + c("cattura_avvia(node)") + ".", lead=True) + \
    table(["Step", "What " + c("kwin_apri()") + " does"], [
        ["1", "Opens the user's Wayland socket with " + c("kwin_display_apri()") + ": " + c("WAYLAND_DISPLAY")
         + " if it answers, otherwise the first " + c("wayland-N") + " in " + c("XDG_RUNTIME_DIR")
         + " that answers (the child is born with an environment composed from scratch)."],
        ["2", "Two round trips: the globals, then the events of the globals just bound (modes, names)."],
        ["3", "If " + c("zkde_screencast_unstable_v1") + " is missing, the gate is closed: the error says which of "
         "the two causes to look at."],
        ["4", "Chooses the first output that has a mode; with none, it fails (without a virtual screen KWin "
         "swallows input too)."],
        ["5", c("stream_output(output, PUNTATORE_METADATO)") + " — the listener is attached immediately, because "
         + c("failed") + " can be sent synchronously."],
        ["6", "Waits for the node at most " + c("ATTESA_NODO_MS") + " = 5000 ms; a refusal or a timeout is an error."],
    ], "«TAB» — Opening the KWin stream") + \
    p("<b>The gate.</b> KWin announces " + c("zkde_screencast_unstable_v1") + " only to a client whose "
      "executable (" + c("/proc/<pid>/exe") + ", canonical) appears in the " + c("Exec=") + " line of a "
      + c(".desktop") + " file that lists the protocol in " + c("X-KDE-Wayland-Interfaces") + ". Measured on "
      "18 Sep 2026 in the " + c("kde") + " test box: without the file the global is absent (58 others are "
      "there), with the file it appears, even when written while the session is running. Since phase 17 the "
      "package installs " + c("/usr/share/applications/org.kde.remotix.desktop") + " and the server only "
      "<i>verifies</i> it at startup with " + c("kwin_verifica_permesso()") + " (file present, " + c("Exec=")
      + " pointing to the running binary, protocol declared); it never writes it. The child is an "
      + c("execve") + " of the same binary, so it is the process KWin recognises. KWin's environment also needs "
      + c("XDG_MENU_PREFIX=plasma-") + ", or its service index is built empty.") + \
    p("<b>The size.</b> KWin on a machine without a seat starts only with the " + c("--virtual") + " backend, "
      "and there the output is decided by the command line: " + c("kwin_wayland_wrapper --xwayland --virtual "
      "--width W --height H --no-lockscreen") + ", written by " + c("sessione.c") + " with the size of the "
      "client that creates the session. A virtual output cannot be resized afterwards, so "
      + c("misura_del_palco()") + " captures the size KWin reports (" + c("kwin_misura()") + ") and logs that "
      "the page will rescale.") + \
    p("<b>The cursor.</b> The mode is fixed for the life of the stream; REMOTIX asks for metadata (4), like "
      "Mutter. The price is that every pointer movement produces a buffer without new pixels marked "
      + c("SPA_CHUNK_FLAG_CORRUPTED") + "; " + c("cattura.c") + " discards those and counts them as "
      + c("solo_cursore") + ". With " + c("--virtual") + " KWin draws the pointer into the image, so the session "
      "runs with REMOTIX's encoded cursor theme (" + rif("The encoded cursor theme") + "), and the child calls "
      + c("cattura_cursore_mai_nascondere()") + ": an empty metadata image is never forwarded as “hidden”, "
      "otherwise the page would remove the browser's own pointer too (the user's test of 20 Sep 2026: “the "
      "pointer is gone”). The declared price: on Plasma an application that hides the cursor does not hide it "
      "for the viewer.")

# ── 6.5 ─────────────────────────────────────────────────────────────────────
S5 = p("On GNOME and KDE the capture is a PipeWire consumer created by " + c("cattura_avvia()")
       + " on the node the compositor announced. Everything is declared in the format proposal "
       "(" + c("proposta()") + ") and in the consumption parameters (" + c("parametri_di_consumo()") + ").",
       lead=True) + \
    table(["Parameter", "What is proposed", "Why"], [
        ["Pixel format", c("BGRx") + " then " + c("BGRA") + " (" + c("CATTURA_COLORE_BGRX")
         + "); the 10-bit request proposes only the four 10-bit formats",
         "Only what the chain can read is listed: an RGB variant chosen by the compositor would swap red and "
         "blue silently. Mutter 48.7 offers only BGRx and BGRA (8 bits)."],
        ["Size", "A fixed rectangle", "An open range lets Mutter choose, and it chooses 1280×720."],
        ["Frame rate", c("0/1") + ", maximum 1…60", "Frames on change, never at a fixed rate."],
        ["Modifier (GPU path)", c("DRM_FORMAT_MOD_LINEAR") + " first, then the encoder's modifiers when the "
         "card refuses linear, then " + c("DRM_FORMAT_MOD_INVALID") + "; flags " + c("MANDATORY | DONT_FIXATE"),
         "LINEAR first is a lesson from kpipewire: RadeonSI rejects DCC buffers, iHD accepts them and forces "
         "LINEAR internally. INVALID means “you decide and tell me”."],
        ["Buffers", "GPU path: 6 (minimum 4, maximum 8), " + c("SPA_DATA_DmaBuf") + " only. Memory path: 4 "
         "(minimum 2), " + c("MemFd") + " and " + c("MemPtr"), "On the GPU path REMOTIX retains up to two "
         "buffers while the encoder reads them; with four the producer would be left with two."],
        ["Header metadata", c("SPA_META_Header"), "Sequence number and timestamp of each frame."],
        ["Damage metadata", "16 regions (range 1–32)", "Mutter logged «Not enough buffers (4) to accommodate "
         "damaged regions (6)»: those “buffers” are region slots, and when they run out Mutter declares the "
         "whole frame damaged — exactly in the case where damage matters."],
        ["Cursor metadata", "Up to " + c("CURSORE_META_BYTE(384, 384)"), "Mutter allocates 384×384; the wire "
         "limit of 256 is enforced in " + c("cursore.c") + "."],
    ], "«TAB» — The PipeWire negotiation") + \
    note("NVIDIA with GNOME 50 (6 Oct 2026): the proposal LINEAR + INVALID ended in «no more input formats» — "
         "Mutter agreed on INVALID, could not allocate it and withdrew it — and the session was black. Now "
         + c("modificatori_per_la_strada()") + " asks the card whether it refuses a linear render buffer "
         "(" + c("vulkanvideo_scheda_rifiuta_il_lineare()") + "); only then it passes the modifiers the Vulkan "
         "encoder can import to " + c("cattura_modificatori_scheda()") + ", and they are proposed between LINEAR "
         "and INVALID. Measured: modifier " + c("0x300000000606014") + " agreed, zero copy. On Intel and Radeon "
         "the proposal is unchanged.", "The card that refuses linear.") + \
    p("<b>Buffer generation.</b> Every time PipeWire reallocates its buffers (renegotiation, wake-up) "
      + c("su_buffer_aggiunto()") + "/" + c("su_buffer_tolto()") + " change a generation counter that travels "
      "with every frame (" + c("generazione") + "). The encoder caches the import of each DMA-BUF, and file "
      "descriptor numbers are recycled: a cache keyed on the descriptor alone would hand the encoder a surface "
      "pointing to a freed buffer, i.e. an old image, with no error. When the generation changes, the cache is "
      "thrown away.") + \
    p("<b>Retention.</b> On the GPU path the " + c("pw_buffer") + " is kept until " + c("cattura_fermo_libera()")
      + ", which the child calls only after " + c("codificatore_comprimi_scheda()") + " has returned — after the "
      "GPU has <i>finished</i> reading, not after the work was queued. Releasing earlier is the defect recorded "
      "in " + c("LEZIONI.md") + " §8: two screens alternating and no error. " + c("rendi_ritenuta()") + " gives "
      "the buffer back only if its generation is still current.") + \
    h4("Resizing a live stream") + \
    p(c("cattura_ridimensiona()") + " rebuilds the proposal at the new size and calls "
      + c("pw_stream_update_params()") + " — what gnome-remote-desktop does — without touching the session or "
      "the virtual monitor. It returns " + c("CATTURA_RITELA_CHIESTA") + ", " + c("CATTURA_RITELA_GIA_COSI")
      + " (the size is already in force: renegotiating it would chase its own tail) or "
      + c("CATTURA_RITELA_GUASTO") + ". “Requested” is not “done”: the truth is told by the next frame at the new "
      "size, a rule taken from neatvnc. Measured with " + c("banchi/04-in8-misura.c") + " on 14 Aug 2026: first "
      "new frame after 41.6 ms on Mutter, no black, 20 resizes in 2 s all exact; 5.1 ms and 0 lost frames out "
      "of 25 on labwc. A size the producer cannot hold kills the stream about 2 ms later («no more input "
      "formats», PipeWire 1.4.2); " + c("cattura_prendi()") + " looks at the state before waiting, so the "
      "failure surfaces in one loop turn (8.1 ms measured) instead of a timeout. The size rule itself "
      "(320×240 to 4096×2304, even sides, larger requests reduced) lives in " + c("rcp_misura_ammessa()")
      + ", see " + rif("The RCP/1 protocol") + ".") + \
    h4("Waking a still desktop") + \
    p("A Wayland compositor delivers only when the scene changes, and a desktop just started is still. Measured "
      "on 14 Aug 2026: 4.4 s between login and the first frame, with a key request every 200 ms and 659 empty "
      "waits. Wayland has no “repaint now”, but restarting the stream makes a buffer arrive. "
      + c("cattura_risveglia()") + " repeats the current parameters at the negotiated size; on labwc it asks "
      "for the next frame whole (" + c("wlr_forza_intero()") + "). The child calls it only when a keyframe is "
      "owed and the capture returned zero, and at most every " + c("RISVEGLIO_MS") + " = 400 ms.") + \
    warn("on Mutter the renegotiation recreates the absolute input devices (" + c("viewports-changed") + " → "
         + c("remove_viewport_devices()") + ", which does not go through " + c("drop_device()") + "). Measured "
         "with " + c("banchi/06-b33-risveglio.c") + ": three wake-ups, three device replacements. If a button is "
         "held at that moment it stays pressed inside Mutter and the desktop never takes another click. The "
         "child therefore does not wake the stream while " + c("input_premuti()") + " reports a key or button "
         "held; the price, declared, is that a client just attached may see a blank page until the user lets "
         "go.", "Wake-up and held buttons.") + \
    p("<b>When the compositor refuses the GPU path.</b> In a machine without 3D acceleration (a VM with "
      + c("virtio-vga") + " without virgl) the compositor renders in software and has no DMA-BUF to offer; the "
      "GPU proposal dies with «no more input formats» (measured 29 Sep 2026 on 7 VMs out of 7). "
      + c("cattura_formato_rifiutato()") + " recognises the facts (stream in error with no format ever agreed, "
      "or a format agreed and no frame ever delivered) and " + c("cattura_avvia()") + " returns "
      + c("G_IO_ERROR_NOT_SUPPORTED") + " when it sees the refusal itself. " + c("ripiega_se_rifiutata()")
      + " in the child then switches to memory, logs it, and never tries the GPU again in that process. The two "
      "paths are never offered together: the compositor would choose, and zero copy would be lost where it "
      "works. Silence (no frame in 5 s) does not trigger the fallback; only a refusal does.")

# ── 6.6 ─────────────────────────────────────────────────────────────────────
S6 = p("labwc has no PipeWire node. It offers " + c("zwlr_screencopy_manager_v1") + " (version 3), and every "
       "frame is a full round trip: " + c("capture_output") + " → " + c("buffer") + " → " + c("copy") + " → "
       + c("ready") + ". The frame rate is therefore REMOTIX's loop, not a property of the compositor — the "
       "user's decision of 20 Sep 2026 (“we ask for them”), which also bought control of the pointer and of the "
       "output size.", lead=True) + \
    p("<b>Why a separate module.</b> " + c("cattura.c") + " was built on the push direction and " + c("figlio.c")
      + " uses it in 35 places; rewriting them two ways would have put GNOME and KDE at risk to serve the new "
      "desktops. The shape copies the clipboard's precedent (" + c("appunti_apri()") + " / "
      + c("appunti_apri_kde()") + "): a second constructor, " + c("cattura_avvia_wlr()") + ", and every public "
      "function of " + c("cattura.c") + " hands over to " + c("wlroots.c") + " at the top when the capture is a "
      "wlroots one. Everything downstream (" + c("cattura_prendi()") + ", " + c("cattura_consegna()")
      + ", the counters) sees no difference.") + \
    table(["Topic", "What happens"], [
        ["Gate", "None. Measured 20 Sep 2026 in " + c("rete11-xfce") + ": a bare client sees 47 globals, "
         "screencopy v3 among them. The only gate is the uid."],
        ["Deprecation", "The protocol is deprecated upstream in favour of " + c("ext-image-copy-capture-v1")
         + ", but labwc on Debian trixie does not expose that one (20 Sep 2026). The module is written so that the "
         "successor can enter beside it: its interface names frames and sizes, not protocol messages."],
        ["Opening", c("wlr_apri()") + " connects (same socket search as KWin), checks the manager and chooses the "
         "output, but captures nothing: “the compositor is not there” and “the first frame does not come” "
         "remain two diagnoses."],
        ["Request", c("capture_output(overlay_cursor = 1, output)") + ": the pointer is drawn into the image. "
         "Frames are copied with " + c("copy_with_damage") + " (the compositor answers only when something "
         "changed); " + c("wlr_forza_intero()") + " makes the next copy a plain " + c("copy") + "."],
        ["Pending frame", "The child waits 8 ms per turn and a round trip costs 9–15 ms. A wait that expires does "
         "not throw the frame away: the request stays alive and the next call resumes it. A damage copy that "
         "is still waiting on a still screen is abandoned when a whole frame is forced."],
        ["Outcomes", c("WLR_FOTOGRAMMA_PRESO") + ", " + c("WLR_FOTOGRAMMA_FALLITO") + " (the compositor sent "
         + c("failed") + "), " + c("WLR_FOTOGRAMMA_SCADUTO") + " (could not look), " + c("WLR_FOTOGRAMMA_ROTTO")
         + " (the connection fell): “the compositor said no” is never confused with “I could not ask”."],
        ["Pixel order", "The " + c("buffer") + " event speaks " + c("wl_shm") + " numbering (0 and 1 special); "
         + c("shm_a_drm()") + " translates it. labwc offers only " + c("XBGR8888") + " (R G B x) in memory, so the "
         "encoder is told " + c("CODIFICATORE_PIXEL_RGBX") + " — without it red and blue were swapped with no "
         "error. On the GPU path labwc gives " + c("XRGB8888") + " (B G R x). On NVIDIA labwc offered only the "
         "24-bit " + c("BG24") + " in memory; " + c("allarga_24()") + " widens it to 32 bits (measured 5 Oct 2026)."],
        ["Orientation", "The " + c("flags") + " event can say the rows are bottom-up (" + c("y_invertita") + "); "
         "ignoring it gives an upside-down image that looks like an encoder fault."],
        ["Size", "A headless labwc output is born 1280×720. " + c("wlr_misura_chiedi()") + " uses "
         + c("zwlr_output_manager_v1") + " (v4 on labwc) and returns " + c("WLR_MISURA_CHIESTA") + ", "
         + c("WLR_MISURA_GIA_COSI") + ", " + c("WLR_MISURA_RIFIUTATA") + " (" + c("failed") + "), "
         + c("WLR_MISURA_ANNULLATA") + " (" + c("cancelled") + ": stale serial, retry) or "
         + c("WLR_MISURA_IMPOSSIBILE") + ". Asking for the size the output already has answers “succeeded” with "
         "no event, so the next frame is the only witness. Other heads are re-confirmed as they are, because "
         "with two outputs a configuration that names one dies with " + c("unconfigured_head") + "."],
    ], "«TAB» — The wlroots capture") + \
    p("The first draft of " + c("wlroots.c") + " passed its bench (530 frames) and still had seven defects; they "
      "were found by an adversarial review on 21 Sep 2026 and shaped the file: wrong format numbering, frames "
      "thrown away at every timeout, three unbounded " + c("wl_display_roundtrip") + " calls, " + c("failed")
      + " and " + c("cancelled") + " in one branch, head discovery depending on event order, a configuration "
      "enabling one head only, and leaks on close.")

# ── 6.7 ─────────────────────────────────────────────────────────────────────
LASTRE = fig(
    box(40, 40, 180, 60, "FREE", "may be named in a copy", "green")
    + box(360, 40, 180, 60, "IN FLIGHT", "named in the current copy", "blue")
    + box(680, 40, 180, 60, "IN HAND", "delivered to the encoder", "navy")
    + arrow(222, 70, 358, 70, label="capture_output + copy")
    + arrow(542, 70, 678, 70, label="ready + GPU fence")
    + path([(770, 102), (770, 150), (130, 150), (130, 102)], label="wlr_rendi() after the encoder returns", lx=450, ly=142)
    + path([(450, 102), (450, 186), (60, 186), (60, 102)], "#d97706", True,
           label="failed or connection lost: the slab is dirty, rebuilt", lx=300, ly=204),
    900, 216, "«FIG» — The three states of a slab; a slab in hand is never named in a copy")

S7 = p("On labwc the zero-copy path is a <i>copy</i> into a DMA-BUF that REMOTIX owns: a “slab” (" + c("lastra")
       + ") is a GBM buffer allocated on the compositor's render node, its DMA-BUF descriptor and the "
       + c("wl_buffer") + " that names it. It is enabled by " + c("wlr_chiedi_la_scheda()") + ", which says no in "
       "writing if it cannot, leaving memory as a declared fallback.", lead=True) + \
    table(["", "A — copy into our own DMA-BUF (chosen)", "B — " + c("zwlr_export_dmabuf_manager_v1")], [
        ["Who owns the buffer", "REMOTIX: allocated, kept until the encoder has finished, named in a copy only "
         "when free", "The compositor: buffers of its own swap chain, reused every turn, always "
         + c("TRANSIENT")],
        ["Cost", "One blit on the GPU (" + c("frame_dma_copy") + " in wlroots 0.18.2); no " + c("glReadPixels")
         + ", which would block the compositor loop", "No copy, but no lever on reuse: the GNOME R29 trap in pure "
         "form"],
        ["New dependency", c("gbm") + " (already present wherever labwc runs) and the " + c("linux-dmabuf")
         + " protocol", "—"],
    ], "«TAB» — The two ways to get a DMA-BUF from labwc") + LASTRE + \
    ul(["<b>Three slabs</b> (" + c("WLR_LASTRE") + "): one in hand, one in flight, one as cheap insurance (8 MB at "
        "1080p). If all are in hand the frame stops and says so; a slab in hand is never recycled.",
        "<b>Linear modifier.</b> The " + c("linux_dmabuf") + " event carries format and size, not modifiers, so "
        "slabs are LINEAR, which every card can read and write. The exception is a card whose GBM refuses "
        "LINEAR|RENDERING (NVIDIA, driver 595): there the slab is allocated with one of the modifiers the Vulkan "
        "encoder imports (measured 5 Oct 2026 on an RTX 4090: 0 of 34 frames before the cure, 28 of 28 after; "
        "about 22 ms capture-to-bytes at 60/s against about 90 ms and 11/s from memory).",
        "<b>Exact format.</b> The slab is allocated in exactly the format and size of the " + c("linux_dmabuf")
        + " event; anything else is " + c("invalid buffer") + ", a protocol error that kills the connection.",
        "<b>Synchronisation.</b> wlroots ends the blit with " + c("glFlush()") + " and sends " + c("ready")
        + " at once, and labwc offers no explicit-sync protocol. After " + c("ready") + " REMOTIX extracts the "
        "fence from the DMA-BUF (" + c("DMA_BUF_IOCTL_EXPORT_SYNC_FILE") + " with " + c("DMA_BUF_SYNC_READ")
        + ") and " + c("poll()") + "s it; the wait is " + c("us_attesa_gpu") + ". Without the ioctl (kernel "
        "older than 5.20) it is said once and implicit sync is trusted.",
        "<b>Generation.</b> Every slab that is born or dies changes the generation, for the same descriptor "
        "reuse reason as on PipeWire.",
        "<b>Switching off.</b> Three consecutive " + c("failed") + " on the GPU path (" + c("WLR_SCHEDA_FALLITI_MAX")
        + ") turn it off, and the log says so; the first slab birth may take up to "
        + c("WLR_LASTRA_NASCITA_S") + " = 1 s."]) + \
    warn("when the encoder is Vulkan, slabs are born at the maximum canvas, " + c("WLR_LASTRA_L") + " × "
         + c("WLR_LASTRA_A") + " = 4096×2304, and a resize changes only the " + c("wl_buffer") + ", never the GBM "
         "object. On the Radeon, GBM (radeonsi) and Vulkan (RADV) in the same process share one "
         + c("amdgpu_device") + ", one GPU address space; freeing a GBM buffer right before a new Vulkan encoder "
         "is created at the new size caused a page fault inside the new input image, "
         + c("VK_ERROR_DEVICE_LOST") + " and a MODE1 reset of the card for everybody (a driver defect, avoided "
         "here). Measured on 1 Oct 2026 (test F-018, LXQt, Radeon RX 6800, Vulkan): 10 faults in 14 runs with "
         "slabs freed on resize, 0 in 5 with slabs kept, 0 in 5 on the memory path. The cost is 3 × 4096 × 2304 "
         "× 4 = 113 MB per session even at 1080p, so it applies only when the child's encoder is Vulkan: "
         + c("lastre_per_la_strada()") + " decides once, before the first stage, through "
         + c("wlr_lastre_alla_tela_massima()") + ". With VA-API the slabs keep the canvas size.",
         "Slabs and the Radeon GPU hang.")

# ── 6.8 ─────────────────────────────────────────────────────────────────────
STRADE = fig(
    zone(20, 12, 860, 112, "GPU path (default, COPIA_ZERO = 1)")
    + box(40, 46, 190, 60, "Compositor", "frame already on the GPU", "navy")
    + box(265, 46, 190, 60, "DMA-BUF", "retained or slab in hand", "blue")
    + box(490, 46, 170, 60, "Import (cached)", "VA surface / VkImage", "blue")
    + box(690, 46, 170, 60, "Convert + encode", "VPP or shader, GPU", "light")
    + arrow(232, 76, 263, 76) + arrow(457, 76, 488, 76) + arrow(662, 76, 688, 76)
    + zone(20, 140, 860, 112, "Memory path (declared fallback)")
    + box(40, 174, 190, 60, "Compositor", "MemFd / wl_shm", "dark")
    + box(265, 174, 190, 60, "memcpy", "in the RT callback", "grey")
    + box(490, 174, 170, 60, "BT.709 in CPU", "colori709.c (VA-API)", "grey")
    + box(690, 174, 170, 60, "Upload + encode", "planes to the GPU", "light")
    + arrow(232, 204, 263, 204) + arrow(457, 204, 488, 204) + arrow(662, 204, 688, 204),
    900, 264, "«FIG» — The two paths of a frame; on Vulkan the memory path uploads RGB and the same shader converts")

S8 = p("“Zero copy” means the frame never leaves the GPU between the compositor and the encoder. It is the "
       "default (" + c("COPIA_ZERO") + " = 1 in " + c("figlio.c") + "; a build-time " + c("-DCOPIA_ZERO=0")
       + " exists only to rebuild the “before” for A/B benches, it is not a product switch). It is not zero "
       "work: the RGB→YUV conversion still happens, on the GPU.", lead=True) + STRADE + \
    p("Why it matters, measured inside the product on 22 Aug 2026 (test server, 1920×1080, 2,450 frames, HEVC on "
      "the GPU): on the old memory path the frame left the GPU, was copied (1.65 ms), converted in CPU (8.15 ms) "
      "and uploaded again (1.16 ms) — 10.96 ms of an 18.86 ms path, 58 %. After zero copy (phase 8, same day, "
      "alternated A/B runs): capture → bytes out 6.41 ms, with copy 0.00, conversion on the GPU 2.98 and upload "
      "0.00; the user's measure of pointer lag dropped to 0.16 title-bar heights, 1.23 times the local desktop "
      "(0.13). Those numbers were taken with libavcodec; phase 18 later showed the GPU path gives identical "
      "bytes and times without it (" + rif("Removing ffmpeg and the CPU path") + ").") + \
    table(["The GPU path is abandoned when…", "Detected by", "Consequence"], [
        ["The compositor has no DMA-BUF to offer (no 3D acceleration)", c("cattura_formato_rifiutato()")
         + ", " + c("G_IO_ERROR_NOT_SUPPORTED"), "Memory for the whole process (" + c("scheda_mai_piu") + ")"],
        ["The measured stride is not a multiple of 64 bytes", c("codificatore_stride_importabile()") + " on the "
         "first frame", "Memory for this canvas only (" + c("scheda_negata_l") + "/" + c("scheda_negata_a")
         + "); the GPU path is retried by itself on the next canvas"],
        ["The encoder is not on the GPU", c("codificatore_in_hardware()"), "Memory for the whole process; since "
         "phase 19 this cannot happen, but the guard costs one line"],
        ["Three " + c("failed") + " in a row on labwc slabs", c("wlroots.c"), "Memory, logged"],
    ], "«TAB» — When the frame goes through memory") + \
    p("<b>The 64-byte stride.</b> The Intel iHD driver, importing a DMA-BUF, does not honour a stride that is "
      "not a multiple of 64 bytes: it reads rows at its own pitch and the desktop comes out blurred and slanted "
      "while the milliseconds look perfect. Measured on 22 Aug 2026 with the certified mark reader "
      "(" + c("banchi/03-marca.py") + "): 1920×1080 (stride 7680) and 1552×888 (6208) read with contrast 1.000; "
      "1544×888 (6176) and 1560×888 (6240) do not read (0.617 and 0.510). 1552 and 1544 are eight pixels apart "
      "with opposite verdicts. The colour statistics of the two streams matched within 0.17 levels out of 255 "
      "while the mark was readable on 0 frames out of 869: an instrument looking at averages says green on this "
      "defect. The producer makes the stride equal to " + c("width × 4") + ", so the code refuses the path and "
      "declares it, rather than sending a wrong image.") + \
    p("<b>Remounting only the capture.</b> Switching path does not tear down the stage. "
      + c("rimonta_solo_la_cattura()") + " stops and reopens only the " + c("Cattura") + " (and its cursor "
      "hook), keeping the input channel, the clipboard and the " + c("RemoteDesktop") + " session: on 25 Aug "
      "2026 a full teardown 33 ms after the EIS channel was opened crashed the child inside "
      + c("ei_disconnect()") + " (SIGSEGV, core read with gdb). On labwc the capture <i>is</i> the source, so "
      "remounting means " + c("cattura_ferma()") + " and " + c("cattura_avvia_wlr()") + ".") + \
    note("the frame rate is one number, " + c("MOVIMENTO_FPS") + " = 60, used both for the capture maximum and for "
         "the encoder; the capture asked 60 and the encoder declared 30 until both were tied to the same name. "
         "The child waits " + c("MOVIMENTO_ATTESA_S") + " = 8 ms per turn: it was 250 ms, and on a still desktop "
         "a click could wait up to a quarter of a second in the socket (measured 15 Aug 2026 on 25 real clicks: "
         "median 136 ms, worst 502 ms).", "One frame rate, short waits.")

# ── 6.9 ─────────────────────────────────────────────────────────────────────
S9 = p("The pointer is drawn by the page, not baked into the video: the image stays clean (two pointers are "
       "worse than one) and the shape travels as a side channel, the " + c("CURSORE_FORMA") + " message of RCP/1. "
       "The capture's only addition to its interface is " + c("cattura_cursore()") + ", which registers the "
       "receiver; " + c("cursore.c") + " sits between PipeWire and the wire.", lead=True) + \
    table(["State", "Metadata", "What is sent"], [
        ["Not received", "No cursor metadata in the buffer", "Nothing; " + c("cattura.c") + " counts it ("
         + c("cursore_assente") + ") and the page keeps its own pointer"],
        ["Hidden", c("id = 0") + ", or a bitmap with no visible pixel (Mutter zeroes the bitmap it just wrote: the "
         "intention is “no image”)", c("CURSORE_FORMA") + " 0×0 with hotspot 0,0 — unless "
         + c("cursore_mai_nascondere()") + " is on (KDE)"],
        ["Unchanged", c("bitmap_offset = 0") + " (the metadata comes with every buffer)", "Nothing; the series "
         "number grows only on a real change"],
        ["Changed", "A new bitmap", "The shape, converted from RGBA to BGRA premultiplied, cropped to 256×256 "
         "(" + c("CURSORE_MAX_LATO") + ") and the crop logged"],
    ], "«TAB» — The four cursor states that cursore.c separates") + \
    p("After a hidden period Mutter sends “unchanged” when the pointer comes back, so " + c("cursore.c")
      + " keeps the last visible shape and re-sends it; otherwise the pointer would stay invisible with no error. "
      "A cursor larger than 256 would make the receiver close the session with " + c("ERRORE_PROTOCOLLO")
      + ", which is why the limit is enforced on this side. A malformed metadata block is declared in the log "
      "and nothing is sent.") + \
    table(["Desktop", "Where the shape comes from"], [
        ["GNOME", "Mutter's metadata, a real bitmap from its theme (Adwaita). The session sets no "
         + c("XCURSOR_*") + " variable."],
        ["KDE Plasma", "KWin's metadata (mode 4). KWin " + c("--virtual") + " also paints the pointer into the image, "
         "so the session runs with REMOTIX's encoded theme: the metadata is a single opaque pixel whose colour "
         "names the shape, and " + c("cursore.c") + " replaces it with the real image (" + c("forma_da_pixel()")
         + ", " + c("forma_immagine()") + ")."],
        ["XFCE, LXQt", "No cursor channel in screencopy. After every injected pointer gesture the child calls "
         + c("cattura_sonda_puntatore()") + "; a 3×3 region capture around the hotspot reads the encoded pixel, "
         "and the shape is delivered from " + c("cattura_prendi()") + " on the child's thread."],
    ], "«TAB» — The pointer shape on each desktop")

# ── 6.10 ────────────────────────────────────────────────────────────────────
S10 = p("Until 24 Sep 2026 the real pointer shape (resize arrows on a border, the I-beam on text, the hand on "
        "links) reached the browser only on GNOME. The user decided it must reach it on all four desktops, and "
        "the design approved was an <b>encoded theme plus a dictionary</b> (" + c("forma.h") + ", "
        + c("forma.c") + ").", lead=True) + \
    p("KWin and labwc draw the pointer into the captured image, so their sessions already ran with an invisible "
      "cursor theme made of 1×1 transparent images. The compositor drew nothing, and the metadata carried the "
      "same nothing. In the encoded theme each shape is still a 1×1 image, but <b>opaque</b> and of a colour of "
      "its own. The server writes the theme before the desktop starts; the child reads the colour and looks up "
      "the real image in a real theme on disk.") + \
    table(["Item", "Value"], [
        ["Theme name", c("FORMA_TEMA") + " = " + c("remotix-invisibile") + " (unchanged, so the sessions' "
         + c("XCURSOR_THEME") + " did not change by one letter)"],
        ["Where", c("<runtime>/remotix/icons/remotix-invisibile/") + " written by " + c("forma_tema_scrivi()")
         + "; " + c("<runtime>/remotix/icons") + " goes into " + c("XCURSOR_PATH") + "; no " + c("Inherits=")
         + " (inheriting would put back real cursors that carry no code)"],
        ["Shapes", c("FORMA_QUANTE") + " = 78 (68 until 24 Sep 2026; labwc's CSS border names added). The index "
         "is the code: new names are appended, never inserted"],
        ["Colour of shape i", "red = 0x40 + i, green = 0xA5 xor i, blue = (7·i mod 256) xor 0x5A, alpha 0xFF. Red "
         "alone distinguishes them and stays away from black and white (the colours real cursors are made of); "
         "green and blue are the check. Lookup is exact to the byte: neighbours differ by 1"],
        ["Real themes", "Adwaita, then " + c("breeze_cursors") + "; name, then aliases, then the arrow. "
         "Measured: Adwaita (62 cursors) is in all four test boxes, " + c("breeze_cursors") + " only in KDE"],
        ["Nominal size", c("FORMA_MISURA") + " = 24, the " + c("XCURSOR_SIZE") + " the sessions declare"],
        ["Parser", "Xcursor 1.0 read by REMOTIX (four tables of little-endian integers), not " + c("libXcursor")
         + ", which brings X11 with it; files over 8 MB are refused"],
    ], "«TAB» — The encoded cursor theme") + \
    p("<b>The labwc probe.</b> " + c("wlr_sonda_puntatore()") + " runs a " + c("capture_output_region")
      + " of 3×3 pixels around the hotspot into a 36-byte " + c("wl_shm") + " buffer (3×3 because the "
      "normalised virtual pointer lands on a fractional pixel); the centre is checked, then the neighbours. "
      "Three rules: only one probe in flight, coalescing to the last position; a plain " + c("copy")
      + ", never with damage; and a <i>tail probe</i> " + c("SONDA_CODA_US") + " = 120 ms after the hand stops, "
      "because a client changes shape after the " + c("enter") + " event that the movement caused. Cost measured "
      "on 24 Sep 2026 (LXQt box, 1344×870, pointer at about 55 Hz for 30 s over qterminal): labwc 4.9–5.1 % CPU "
      "without the probe, 6.3–6.4 % with it, the child +0.5 points, painted frames unchanged (55.0–55.3/s). Under "
      "the 2-point threshold, so thinning (" + c("SONDA_MINIMO_US") + ") stays at 0.") + \
    warn("the compositor now paints one coloured pixel under the hotspot into the image. The browser's pointer "
         "covers it and the encoder smears it; whether it is ever visible is not settled until the user looks. "
         "If the real theme is missing, " + c("forma_immagine()") + " fails once in the log and the client keeps "
         "its own arrow.", "The declared price.")

# ── 6.11 ────────────────────────────────────────────────────────────────────
S11 = p("The constants of the capture, where they live and what set them.", lead=True) + \
    table(["Constant", "Value", "File", "Reason"], [
        [c("MOVIMENTO_FPS"), "60", c("figlio.c"), "Capture maximum and encoder rate; asking 30 gave 18, asking 60 "
         "gave 37 (" + c("LEZIONI.md") + " §6.1)"],
        [c("MOVIMENTO_ATTESA_S"), "0.008 s", c("figlio.c"), "Wait per loop turn; 250 ms added up to a quarter "
         "second to clicks"],
        [c("RISVEGLIO_MS"), "400 ms", c("figlio.c"), "Minimum interval between stream wake-ups"],
        [c("COPIA_ZERO"), "1", c("figlio.c"), "GPU path by default; 0 only to rebuild A/B benches"],
        [c("ATTESA_AGGANCIO_MS"), "10000 ms", c("cattura.c"), "Wait for the PipeWire stream to attach, per attempt"],
        [c("MISURA_PIXEL_OGNI_MS"), "500 ms", c("cattura.c"), "Diagnostic pixel scan cadence (was every frame)"],
        [c("REGIONI_MAX"), "16", c("cattura.c"), "Damage regions carried per frame; beyond, the frame counts as whole"],
        [c("ATTESA_CHIAMATA_MS") + " / " + c("ATTESA_NODO_MS"), "15000 / 10000 ms", c("mutter.c"),
         "D-Bus call and node announcement"],
        [c("ATTESA_NODO_MS"), "5000 ms", c("kwin.c"), "Node announcement from KWin"],
        [c("PUNTATORE_METADATO"), "4", c("kwin.c"), "Cursor as metadata"],
        [c("WLR_LASTRE"), "3", c("wlroots.c"), "Slabs: in hand, in flight, insurance"],
        [c("WLR_SCHEDA_FALLITI_MAX"), "3", c("wlroots.c"), "Consecutive failures before the GPU path is switched off"],
        [c("WLR_LASTRA_L") + " × " + c("WLR_LASTRA_A"), "4096 × 2304", c("wlroots.c"),
         "Slab size with Vulkan encoding (= the largest canvas)"],
        [c("SONDA_CODA_US"), "120 ms", c("wlroots.c"), "Tail probe after the last pointer gesture"],
        [c("CURSORE_MAX_LATO"), "256", c("cursore.h"), "Wire limit of " + c("CURSORE_FORMA")],
        [c("FORMA_QUANTE") + " / " + c("FORMA_MISURA"), "78 / 24", c("forma.h"), "Encoded theme"],
    ], "«TAB» — Capture constants") + \
    p("Every capture line in the log carries the area " + c("cattura") + " (also from " + c("kwin.c") + " and "
      + c("wlroots.c") + ": whoever reads the log looks for pixels under one word). The stage assembly line says "
      "which path was mounted, because a “conversion 0.9 ms” on the GPU path and one on the memory path are not "
      "the same quantity; see " + rif("Logging and diagnostics") + ".") + \
    tip("the benches that prove these rules are in " + c("banchi/") + ": " + c("06-b5-esiti-cattura.c")
        + " (capture outcomes, resize failures), " + c("04-in8-misura.c") + " (live resize), "
        + c("06-b33-risveglio.c") + " (wake-up and held buttons), " + c("14-f1-forma.c")
        + " (every colour of the encoded theme), " + c("03-marca.py") + " (the mark reader used for the stride "
        "limit). See " + rif("Testing") + ".", "Benches.")



CHAPTER = ("Screen capture per compositor", [
    ("Capture at a glance", S1),
    ("The capture contract", S2),
    ("GNOME: the Mutter D-Bus sequence", S3),
    ("KDE: the KWin screencast protocol", S4),
    ("PipeWire negotiation, resize and wake-up", S5),
    ("XFCE and LXQt: wlroots screencopy", S6),
    ("Slabs: zero copy on labwc", S7),
    ("Zero copy and the memory fallback", S8),
    ("The cursor channel", S9),
    ("The encoded cursor theme", S10),
    ("Capture constants", S11),
])
