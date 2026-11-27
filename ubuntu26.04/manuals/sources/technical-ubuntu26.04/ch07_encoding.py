from build import arrow, box, c, code, fig, flow, h4, note, p, rif, table, text, tip, ul, warn, zone

# ── 1 ───────────────────────────────────────────────────────────────────────
VIA = fig(
    box(20, 30, 160, 64, "Captured frame", "DMA-BUF or pixels", "navy")
    + box(220, 30, 200, 64, "encoder.c", "one front for two routes", "blue")
    + box(470, 8, 190, 56, "vulkanvideo.c", "Vulkan Video (by capability)", "light")
    + box(470, 74, 190, 56, "vadirect.c", "VA-API via libva (Intel)", "light")
    + box(700, 30, 180, 64, "Annex-B bytes", "checked, then sent", "green")
    + arrow(182, 62, 218, 62) + arrow(422, 52, 468, 36) + arrow(422, 72, 468, 102)
    + arrow(662, 36, 698, 56) + arrow(662, 102, 698, 70)
    + box(220, 150, 200, 50, "colors709.c", "BT.709 in CPU, memory path", "grey")
    + box(470, 150, 190, 50, "shader .comp", "BT.709 on the GPU", "grey")
    + box(700, 150, 180, 50, "bit_writer.c", "SPS/PPS/VPS bits", "grey")
    + arrow(320, 148, 320, 96, "#475569", True) + arrow(565, 148, 565, 132, "#475569", True)
    + arrow(790, 148, 610, 116, "#475569", True)
    + text(450, 228, "No CPU encoder: without a capable GPU the server offers no video codec", 11, "#475569"),
    900, 236, "«FIG» — The encoder: one front, two GPU routes chosen by capability, three helpers")

S1 = p("REMOTIX encodes every frame on the graphics card, in H.264 or HEVC, into Annex-B that the browser's WebCodecs "
       + c("VideoDecoder") + " decodes. " + c("encoder.c") + " is the front: it chooses the route by capability, Vulkan Video if the "
       "card encodes that codec through Vulkan and VA-API otherwise, and it keeps everything that works on the bytes (shape "
       "checks, keyframes, the 16 MiB ceiling, quality steps, the level check) in one place for both routes. There is no software "
       "encoder and no libavcodec: a server without a capable GPU says so at startup and offers no video codec. On Ubuntu 26.04 the "
       "package also contains a GPL-2.0 program, the labwc that hosts KWin on Kubuntu (" + rif("Screen capture") + "); it is a separate "
       "executable and is not linked into the encoder, so «no GPL encoder library» remains true.", lead=True) + VIA + \
    table(["File", "Role"], [
        [c("encoder.c") + " / " + c("encoder.h"), "Opens the encoder by name, chooses the route, converts or imports the input, "
         "checks the bytes, keeps the confession, keyframes, ceiling, resize"],
        [c("vulkanvideo.c") + " / " + c("vulkanvideo.h"), "Vulkan Video: discovery per DRM node, session, parameters, DMA-BUF "
         "import, colour conversion shader, the encode loop"],
        [c("vulkanvideo_rgb_nv12.comp"), "Compute shader RGB to NV12/P010, BT.709 limited; compiled into " + c("vulkanvideo_rgb_nv12_spv.h")
         + ", which is kept in the repository so the product needs no shader compiler"],
        [c("vadirect.c") + " / " + c("vadirect.h"), "libva used directly: configuration, sequence/picture/slice parameters, packed headers, "
         "begin/render/end, the coded buffer"],
        [c("colors709.c") + " / " + c("colors709.h"), "BGRx/RGBx to YUV 4:2:0 BT.709 limited in CPU (SSE2), for the VA-API memory path"],
        [c("bit_writer.c") + " / " + c("bit_writer.h"), "Bit writer: " + c("bw_u()") + ", " + c("bw_ue()") + ", " + c("bw_se()")
         + ", trailing bits, NAL units with emulation prevention"],
        [c("card_pick.c"), "Which card the desktop draws on (the compositor's card; the encoder follows it)"],
        [c("render_node.c"), "Asks the compositor which card it uses, and describes a node for the log"],
        [c("render_grant.c"), "The ACL that lets a stale user manager open the card"],
        [c("child.c") + " (the per-user child)", "Asks for the encoder (" + c("encoder_of()") + "), feeds it, probes the GPU at startup ("
         + c("child_video_capabilities()") + ") and for the package (" + c("--encoding-test") + ")"],
    ], "«TAB» — The files of the encoder") + \
    p("The licensing consequence is stated in " + c("debian/control") + " and " + c("THIRD-PARTY-LICENSES") + ": the product binary "
      "links libva (MIT), the Vulkan loader (Apache-2.0), libgbm and PipeWire, and no GPL encoder library.")

# ── 2 ───────────────────────────────────────────────────────────────────────
S2 = p("RCP/1 numbers the video codecs in the frame header: <b>1 = HEVC, 2 = AV1, 3 = H.264</b>. The enum " + c("CodecVideo")
       + " (" + c("encoder.h") + ") uses the same values so that no conversion table can drift. AV1 is never negotiated and nothing in "
       "the product encodes it, but its number stays reserved, and " + c("encoder.c") + " still carries a reader for AV1 sequence "
       "headers that no route can reach (see " + rif("Appendix C — Known issues and open points") + ").", lead=True) + \
    p("<b>What the server offers is measured, not written.</b> At startup the codec probe opens each codec through the same "
      + c("encoder_of()") + " a session uses and encodes a " + c("PROBE_SIDE") + " = 256 pixel synthetic frame until bytes come out "
      "(at most " + c("PROBE_ROUNDS") + " = 8 attempts). The probe runs in a short-lived process, because a driver that crashes must "
      "not take the server down before it has opened its port. In the default two-process server the <b>root side</b> runs it "
      "(" + c("rootside.c") + ", " + c("child_video_probe_begin()") + " and " + c("child_video_probe_step()") + "), since the network "
      "side runs as the user " + c("remotix") + " and does not open the card, and hands the result to the network side. The result "
      "reaches " + c("rcp_video_codec_set()") + " as " + c("hevc,h264") + ", " + c("hevc") + ", " + c("h264") + " or empty. With an empty "
      "list every " + c("HELLO") + " ends in " + c("NOTHING_IN_COMMON") + " and the startup log says why, with the remedy. A browser "
      "must never be offered a codec the server cannot keep.") + \
    p("<b>The measure is repeated when the card arrives late.</b> If the card's node does not exist at startup (at boot it can "
      "appear after the unit starts), " + c("codec_retry()") + " in " + c("rootside.c") + " measures again in a probe process collected "
      "without blocking the loop: after 2 s (" + c("codec_every_ms") + " starts at 2000), doubling up to 60 s. When something is found it "
      "logs «the card arrived N s after startup», tells the network side, and " + c("video.codec") + " is offered from the next "
      + c("HERE_I_AM") + ". If the node opens but nothing encodes (a driver still loading its firmware), "
      + c("child_video_retry_worthwhile()") + " allows five more tries at the same pace and then one line and stop: not a matter of time. "
      "The single-process server (" + c("--no-split") + ") has the same loop in " + c("main.c") + ".") + \
    table(["Capability", "Page (" + c("page.html") + ")", "Server (" + c("rcp.c") + ")"], [
        [c("video.codec"), "Probed by decoding: " + c("PREFERENCE") + " = " + c("[\"hevc\", \"h264\"]") + ", filtered to the codecs that reach "
         "the pixel in this browser", "The measured list; the negotiated codec is the first entry of the <b>browser's</b> list that the "
         "server also offers (" + c("first_in_common()") + ")"],
        [c("video.depth"), "The depths that painted, in the order 8, 10", c("OUR_DEPTH") + " = " + c("8,10") + "; the client must include 8"],
        [c("video.level"), c("DECLARED_LEVEL") + " = " + c("5.1"), "A ceiling the encoder must respect (" + rif("Bytes, levels and the confession") + ")"],
    ], "«TAB» — The video capabilities exchanged in the handshake") + \
    p("The codec string handed to " + c("VideoDecoder.configure()") + " is built in the page by " + c("codec_strings()") + ": for H.264 "
      + c("avc1.6400") + " plus the level in <i>hexadecimal</i> (5.1 gives " + c("avc1.640033") + ", decimal would give the invalid "
      + c("avc1.100051") + "), for HEVC " + c("hev1.") + " with profile, level and " + c("L93") + " as second choice. The server composes its "
      "own string from the SPS it produced (" + c("codec_string") + " in the confession), and the profile and level bytes are what decoders "
      "use. The browser-side logic is in " + rif("The browser page") + ".") + \
    note("H.264 is <b>High, 8 bit</b> only. " + c("profile_va()") + " returns " + c("VAProfileNone") + " for H.264 at 10 bits instead of "
         "trying, and the Vulkan route refuses it in " + c("vulkan_fit()") + ". HEVC is Main or Main 10. The capture is 8 bits per channel on "
         "every desktop (" + rif("Screen capture") + "), so a 10-bit stream is 8 bits promoted; the confession declares it ("
         + c("promotion_8_to_10") + ").", "Depth.")

# ── 3 ───────────────────────────────────────────────────────────────────────
S3 = p("The encoder is asked for <b>by name</b>, and the name says how the route is chosen. A name that is not one of these six is "
       "refused by " + c("codificatore_nuovo()") + " with the reason: there is no silent fallback to another component, profile or depth.",
       lead=True) + \
    table(["Name", "Route", "Used by"], [
        [c("h264_card") + ", " + c("hevc_card"), "By capability: Vulkan Video if " + c("vulkan_fit()") + " says the card fits this request, "
         "otherwise VA-API (and the log says why)", "The product (default)"],
        [c("h264_vulkan") + ", " + c("hevc_vulkan"), "Vulkan only; failure if unavailable", c("--encoding-route vulkan") + ", diagnosis"],
        [c("h264_vaapi") + ", " + c("hevc_vaapi"), "VA-API only (" + c("vadirect.c") + ")", c("--encoding-route vaapi") + ", diagnosis"],
    ], "«TAB» — The six component names") + \
    p(c("child.c") + " builds the name from the codec and the route in force (" + c("component_of()") + "); the route is " + c("card") + " unless "
      "the server was started with " + c("--encoding-route card|vulkan|vaapi") + ", which the parent repeats on every child's command line (the "
      "child is an " + c("exec") + ", a static of the parent would not reach it). The component actually opened is what " + c("encoder_name()")
      + " and the log report, with the node, the vendor string and the VA-API entry point.") + \
    table(["Condition checked by " + c("vulkan_fit()"), "If it fails"], [
        ["Input is RGB (not the bench format " + c("yuv420p10le") + ")", "VA-API"],
        ["H.264 at 8 bits; codec is H.264 or HEVC", "VA-API"],
        [c("vulkanvideo_capabilities()") + " finds a Vulkan device with an encode queue on the node", "VA-API"],
        ["The profile (H.264 High, HEVC Main, HEVC Main 10) declares encoding", "VA-API"],
        ["The canvas is within the card's minimum and maximum size", "VA-API"],
        ["The rate-control mode needed is declared: CQP without the bandwidth ceiling, VBR with it", "VA-API"],
        ["The current QP is within the card's QP range", "VA-API"],
    ], "«TAB» — When Vulkan Video is taken") + \
    p("<b>The VA-API entry point</b> is a declared rule, " + c("ENCODER_POWER_DECLARED") + " (" + c("RENDER_POWER") + " in " + c("child.c") + "): "
      "low-power " + c("EncSliceLP") + " if the driver declares it for the profile, full " + c("EncSlice") + " otherwise, failure if neither. "
      "The pair (profile, entry point) is read with " + c("vaQueryConfigEntrypoints()") + " before opening, with three outcomes: present, "
      "absent, could not look. The maximum size is read with " + c("vaGetConfigAttributes()") + " at every opening, because another card may "
      "declare less.") + \
    p("<b>When opening fails</b> the child does not retry at every frame: the wait doubles from " + c("ENC_RETRY_MIN_MS") + " = 500 ms to "
      + c("ENC_RETRY_MAX_MS") + " = 10 s and the log says the next attempt time. A second guard, " + c("enc_death_wait_ms()") + " in "
      + c("encbackoff.h") + ", covers an encoder that opens fine and then <i>dies</i> at the first quality change: the count of deaths is kept "
      "apart from the count of failed openings (a successful creation resets the latter), doubles the wait up to the maximum, and goes back to "
      "zero only after a frame was really sent. A full card is not a missing codec: when " + c("vkCreateVideoSessionKHR") + " returns "
      + c("VK_ERROR_TOO_MANY_OBJECTS") + " the log says the card has run out of encode slots, and the session gets its first frame by itself when "
      "one frees.")

# ── 4 ───────────────────────────────────────────────────────────────────────
S4 = p("Two different cards matter. The desktop is drawn by the compositor on <i>its</i> card, and the encoder must open the <i>same</i> card, "
       "or every frame is a cross-card import that fails or goes through memory. REMOTIX therefore chooses the desktop's card itself and then "
       "makes the encoder follow the compositor.", lead=True) + \
    table(["Question", "Answered by", "Rule"], [
        ["Which card does labwc (XFCE, LXQt) or KWin's host (KDE) draw on?", c("card_pick_desktop()") + " in " + c("card_pick.c") + ", called from "
         + c("session.c") + " (and from " + c("wlroots.c") + " as a fallback)", "1. The BIOS primary card (PCI " + c("boot_vga") + " = 1) if capable (its "
         "render node opens and " + c("card_can_draw()") + " holds). 2. Otherwise the capable card with the lowest PCI address, not the lowest node "
         "name. Capable means a buffer is born on it through GBM (XRGB8888, with " + c("GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING") + ", then rendering only)."],
        ["And GNOME?", "Mutter itself", "It chooses its own card; it does not go through " + c("card_pick.c") + "."],
        ["Which card does the encoder open?", c("choose_render_node()") + " in " + c("child.c"), "1. The compositor's card, from the " + c("main_device")
         + " of the " + c("linux_dmabuf") + " v4 feedback (" + c("render_node_of_compositor()") + ", 2 s ceiling). 2. " + c("--render-node")
         + ". 3. " + c("RENDER_NODE") + " = " + c("/dev/dri/renderD128") + ". On a one-card machine the three are the same node."],
    ], "«TAB» — Choosing the card") + \
    p("The choice is made once per session, logged once with the PCI address, the driver and the vendor:device pair (" + c("render_node_describe()") + "), "
      "and latched (" + c("render_node_latched") + ") so that it does not move under an open encoder. " + c("render_node_is_drm()") + " refuses a "
      + c("--render-node") + " that is not a character device with major " + c("RENDER_NODE_DRM_MAJOR") + " = 226 under " + c("/dev/dri/") + ", and "
      + c("render_node_same()") + " compares two names by " + c("st_rdev") + ". When the card is a service or BMC card (" + c("card_pick_service_driver()")
      + ": " + c("ast") + ", " + c("mgag200") + ", " + c("hibmc") + ") the child logs one warning that the desktop probably draws in software; behaviour is "
      "not changed. If no card can create a buffer, " + c("session.c") + " passes " + c("WLR_RENDERER=pixman") + " and says so.") + \
    h4("Access to the card: groups and the render grant") + \
    p("A session has no physical seat, so logind gives it no ACL on the render node, and the user must be in the group that owns " + c("/dev/dri/renderD*")
      + ". At the first connection, after PAM said yes and before the child is forked, the parent adds a user who is not in the group with "
      + c("usermod -aG") + " (only the group of the render nodes, read from " + c("/dev/dri") + ", not " + c("video") + ") and records the enrolment in "
      + c("/var/lib/remotix/group-enrollments.jsonl") + " (" + c("child.c") + "; the policy side is in " + rif("Login and its defences") + "). If the user is "
      "not in the group the log says that the session will be born blind.") + \
    p("A group is read when a process is born. If the user already has a " + c("systemd --user") + " manager (SSH, lingering) it keeps the old list, and so "
      "does gnome-shell or KWin started by it: the desktop would draw in software. " + c("render_grant.c") + " bridges that without closing anything: "
      "for GNOME and KDE only (" + c("child.c") + " tests " + c("desktop_session()") + "), " + c("render_grant_needed()") + " reads the manager's groups from "
      + c("/proc") + " and " + c("/sys/fs/cgroup") + ", and if it cannot open the node " + c("render_grant_add()") + " writes an ACL entry for the user's "
      "<i>primary group</i> on every " + c("renderD*") + " (the " + c("system.posix_acl_access") + " attribute, written directly, so no " + c("setfacl")
      + " is needed) and records it in " + c("/var/lib/remotix/render-grants") + ". XFCE and LXQt need nothing: labwc is born from the child with fresh groups.") + \
    ul(["<b>Group, not user:</b> logind rewrites the named-user entries of those ACLs when the person in front of the machine changes; named-group entries it leaves alone.",
        "<b>Only a provably private group:</b> an ACL for a group shared by several accounts would give the card to all of them. " + c("group_is_private()")
        + " reads " + c("/etc/group") + " and " + c("/etc/passwd") + " only, and anything it cannot judge (a line over " + c("MAX_LINE") + ", a NUL byte, a NIS compat "
        "line starting with " + c("+") + ", a read error) counts as not private. A network account gets no grant, and its desktop is born in software.",
        "<b>Lifetime:</b> the grant lives as long as the child, not the desktop. It is removed when the child ends (" + c("render_grant_remove()") + "), by the start-up "
        "sweep (" + c("render_grant_sweep()") + ") after a crash, and by " + c("remotix --drop-render-grants") + " (" + c("render_grant_drop_all()") + ") at package "
        "removal (" + c("debian/remotix.prerm") + "). The nodes live in devtmpfs, so a reboot clears every ACL.",
        "<b>Declared limits:</b> a device recreated while the desktop lives (driver reload, hotplug) loses the grant; removing the grant does not close descriptors already open."]) + \
    note("NVIDIA's proprietary driver opens the card through " + c("/dev/nvidia*") + " devices with group and mode set by module parameters, not through "
         + c("/dev/dri") + " alone. The code of this tree does not handle that case, and DECISIONS-11.md §11.38 records it as a known limit, not "
         "measured on a real NVIDIA machine for the device files (the rest of the NVIDIA route was measured on Ubuntu 26.04, 5–6 Oct 2026, with an earlier version of the code).", "NVIDIA device files.")

# ── 5 ───────────────────────────────────────────────────────────────────────
S5 = p("The package asks the product itself whether the machine encodes a frame on the GPU. " + c("remotix --encoding-test [h264|hevc] [--node /dev/dri/…] "
       "[--encoding-route vaapi|vulkan|card]") + " (" + c("child_test_encoding()") + ", dispatched from " + c("main.c") + ") goes through "
       + c("encoder_of()") + " with H.264, 8 bits, no level ceiling and BGRx, encodes a 256×256 frame until bytes come out, and prints one JSON "
       "line on stdout (the log goes to stderr):", lead=True) + \
    code('{"outcome":"hardware","encoder":"h264_vaapi","route":"vaapi","node":"/dev/dri/renderD128",\n'
         ' "reason":"…","codec":"h264","offered":"hevc,h264","hevc":"hardware","h264":"hardware",\n'
         ' "hevc_route":"vaapi","h264_route":"vaapi"}', "text", "The probe's answer (shape; keys as printed by test_exits() in child.c)") + \
    p(c("outcome") + " is " + c("hardware") + " or " + c("none") + "; " + c("encoder") + " is the component opened; " + c("route") + " the route that encoded; "
      + c("node") + " the render node; " + c("reason") + " the reason in words; " + c("offered") + " what the server would offer the browser with the same "
      "arguments; " + c("hevc") + " and " + c("h264") + " with " + c("hevc_route") + " and " + c("h264_route") + " give the same answer per codec.") + \
    table(["Exit code", "Meaning"], [
        ["0", "The GPU encoded a frame and the bytes were read back"],
        ["1", "The GPU opens but no frame came out, or it cannot be told whether it is right"],
        ["2", "Usage error"],
        ["3", c("PROBE_NO_CARD") + ": no GPU can encode this codec (no node, no driver, a driver without encoding)"],
    ], "«TAB» — Exit codes of --encoding-test") + \
    p("«hardware» is said only if the component accepts GPU surfaces (" + c("codificatore_in_hardware()") + "), a frame came out with bytes, and the bytes "
      "were read back (" + c("read_from_stream") + "). The frames of the test are shared with the startup probe and with the per-session test of "
      + c("node_of_codec()") + " (" + c("probe_frames()") + "): one test, not two that drift. Permissions matter: without the node's group a user sees "
      + c("none") + " where root would see " + c("hardware") + ", so the probe must run with the identity in question.") + \
    p("<b>Where the package uses it.</b> " + c("debian/remotix.preinst") + " refuses a <i>new</i> installation when the kernel lists no DRM render node "
      "(" + c("/sys/class/drm/renderD*") + "), and " + c("debian/remotix.postinst") + " runs " + c("remotix --encoding-test h264") + " under a 30 s timeout at the "
      "first configuration (with " + c("MESA_SHADER_CACHE_DISABLE=true") + ", so that no shader cache is written in root's folders) and, if it does not exit 0, prints that the card did not encode a test frame and what to check (the message names "
      + c("va-driver-all") + " for Intel and AMD, or NVIDIA's own driver). It never makes " + c("apt") + " fail, because the driver may arrive with "
      "the Recommends configured after the package. On Ubuntu 26.04 " + c("va-driver-all") + " is in <i>universe</i> and pulls only the Intel drivers; "
      "the VA-API driver for AMD comes with Mesa (" + c("mesa-libgallium") + ", in <i>main</i>, which provides " + c("va-driver") + "), so the "
      "package Recommends " + c("va-driver-all") + " alone, without the alternative, or apt would take the Recommends as satisfied by Mesa and an Intel "
      "card would encode nothing (comment of " + c("debian/control") + ", checked in clean containers on 18 Nov 2026). The package is "
      "described in " + rif("The package") + ".") + \
    note("the comment above " + c("test_exits()") + " in " + c("child.c") + " (around line 7055) still lists the per-codec keys as " + c("hevc_strada") + " and "
         + c("h264_strada") + ", but the code prints " + c("hevc_route") + " and " + c("h264_route") + ". The manual follows the code.",
         "Comment against code.")

# ── 6 ───────────────────────────────────────────────────────────────────────
S6 = p(c("vadirect.c") + " talks to libva (MIT) directly and does the four things a media library would: configure the driver, fill the "
       "sequence, picture and slice parameters, write the stream headers, and run begin/render/end for each frame. Its governing rule, from "
       "the file's comments, is to produce the same kind of stream as the library it replaced, field by field, so that the browser receives "
       "what it was tested with.", lead=True) + \
    table(["Choice", "Value", "Why"], [
        ["GOP", c("intra_period") + " = " + c("intra_idr_period") + " = " + c("INT_MAX") + " when " + c("chiavi_ogni") + " (the keyframe interval) is 0",
         "Keyframes only on request (" + rif("Bytes, levels and the confession") + ")"],
        ["B frames", "None: " + c("ip_period") + " = 1", "Latency weighs more than compression: a frame waiting for the next one is a frame of delay"],
        ["References", "1 (" + c("max_num_ref_frames") + "), " + c("REBUILT") + " = 3 reconstructed surfaces", "Current and reference, one turn of margin"],
        ["H.264 SPS", "High (100), constraint_set4 = 1, POC type 2, cropping when the canvas is not a multiple of 16", "As written for a stream without B frames"],
        ["VUI", "Video signal type present, limited range, primaries, transfer and matrix = 1 (" + c("COLOR_PRIMARIES") + ", " + c("COLOR_TRANSFER")
         + ", " + c("COLOR_MATRIX") + ": BT.709), timing, bitstream restriction", "The colour must be declared, not assumed"],
        ["HRD", "Only with the bandwidth ceiling", "—"],
        ["Rate control", c("VA_RC_CQP") + " (QP " + c("QP_HARDWARE") + " = 26) by default; " + c("VA_RC_QVBR") + " with the ceiling",
         "Asked by name and verified against the driver's mask (" + rif("Quality, degradation and budget") + ")"],
        ["Coded buffer", "3 × aligned surface width × height + " + c("CODED_MARGIN") + " (64 KiB)", "An uncompressed frame bounds a compressed one"],
        ["Synchronisation", "Each frame waits for the GPU: " + c("vaSyncBuffer") + " with the ceiling " + c("SYNC_WAIT_NS") + " = 10 s, or " + c("vaSyncSurface") + " on a driver without it, where the wait has no ceiling",
         "No asynchronous depth: the frame that the loop reads back is the frame it just submitted"],
        ["SEI", "A user-data SEI with REMOTIX's UUID (" + c("UUID_REMOTIX") + ") on the first frame", "The page reads only SPS and PPS"],
    ], "«TAB» — The VA-API stream, as vadirect.c writes it") + \
    p("Headers are passed to the driver as <i>packed headers</i>; " + c("VaDirectDeclaration") + " records the mask the driver declares and the one in force, "
      "the surface alignment (16 for H.264, the CTB for HEVC), whether HEVC P frames are coded as generalised-B slices (" + c("p_come_b") + ", iHD) and "
      "the input fourcc (" + c("NV12") + " or " + c("P010") + ").") + \
    note("the comments record that on Mesa radeonsi the driver reads REMOTIX's packed headers and regenerates them, and that the cropping window Mesa "
         "does not write is fixed afterwards on the bytes (" + rif("Bytes, levels and the confession") + "). The comment dates from Mesa 25.0.7; "
         "whether it still holds with Mesa 26.0.8 is not verified, and on the Radeon of the virtual machines the encoder takes the Vulkan route, "
         "so this code path was not exercised there.", "The AMD driver rewrites the headers.") + \
    p("<b>The padding past the canvas.</b> The card encodes a picture a little larger than the screen (the sides are rounded up, H.264 to 16, HEVC "
      "to the coding block; a 1080-row screen goes out as 1088 rows) and the decoder is told to hide the extra strip. The hidden strip still takes part "
      "in the compression, so what is in it can leak into the last visible row or column. " + c("convert_on_gpu()") + " adds, in the same GPU step that "
      "turns RGB into the encoder's YUV, up to three layers that copy the last row, the last column and the corner pixel into the hidden strip. "
      + c("REMOTIX_VPP_PADDING") + " set to " + c("0") + " switches this off (read in " + c("encoder.c") + "); the layers are also dropped for the rest of "
      "the encoder's life if the driver refuses them once. The comments record that with more than one layer AMD changes conversion engine (a shader instead "
      "of the encoder) at a small per-frame cost, and Intel is unchanged; those figures were taken on earlier builds (Mesa 25.0.7 on the AMD side, "
      "ffmpeg as the reference) and were never taken again on Ubuntu 26.04, which has libva 2.23 and Mesa 26.0.8. "
      "A canvas already aligned has no layers.")

# ── 7 ───────────────────────────────────────────────────────────────────────
S7 = p(c("vulkanvideo.c") + " uses " + c("VK_KHR_video_encode_queue") + " with the H.264 and H.265 encode extensions, the Vulkan loader and the system "
       "driver, and nothing else. It is the route for cards whose driver does not encode through VA-API, and every vendor that encodes in Vulkan "
       "gets the same code.", lead=True) + \
    table(["Vendor", "Route today", "Evidence in this tree"], [
        ["AMD with RADV (Mesa)", "Vulkan", "[Measured on Ubuntu 26.04] On the four virtual machines with the Radeon RX 6800 handed over (19 Nov 2026, package " + c("unione10") + "), the journal of the service says «VULKAN VIDEO route on /dev/dri/renderD128 — AMD Radeon RX 6800 (RADV NAVI21) (radv Mesa 26.0.8-1ubuntu0.3, API 1.4) declares HEVC Main up to 8192x4352 … requested by CAPABILITY (Vulkan before VA-API)» and likewise H.264 High up to 4096x4096, and the probe opens " + c("hevc_vulkan") + " and " + c("h264_vulkan") + " (the lines «opened: HEVC 8 bit via hevc_vulkan (in HARDWARE …)»). Earlier measurements in the comments of " + c("encoder.c") + " (1 Oct 2026, RADV, Mesa 25.0.7) were taken on the development server. " + c("SPECS.md") + " §11.4-bis lists AMD on Ubuntu 26.04 as served by the official repositories. The package Recommends " + c("mesa-vulkan-drivers") + " (Mesa 26.0.8, <i>main</i>)."],
        ["Intel (integrated, Arc)", "VA-API", "Chosen by capability: " + c("vulkan_fit()") + " fails on a driver that does not declare encoding, and the Intel path is "
         + c("iHD") + " with " + c("EncSliceLP") + ". [Measured on Ubuntu 26.04] On the real live image of Kubuntu 26.04.1 booted on the server, the startup line read «video.codec offered … hevc,h264 — card /dev/dri/renderD128 (route requested «card») — HEVC: yes via vaapi» (owner's test, 19 Nov 2026, " + c("docs/STORIA-ubuntu-26.04.md") + "). That the card was the server's integrated Intel graphics is a deduction, not a recorded fact: the Radeon is visible on the live image as well. " + c("va-driver-all") + " is a Recommends, in <i>universe</i> on Ubuntu."],
        ["NVIDIA, proprietary driver", "Vulkan, by capability", "NVIDIA cards encode through Vulkan Video with NVIDIA's proprietary driver. Measured on a real card (RTX 4090, driver 595) on 5–6 October 2026, on Ubuntu 26.04, with an earlier version of the same code (the " + c("[M]") + " comments in " + c("src/vulkanvideo.c") + ", " + c("src/child.c") + " and " + c("src/wlroots.c") + "); not run again on this tree."],
    ], "«TAB» — Which cards take which route") + \
    table(["Aspect", "What vulkanvideo.c does"], [
        ["Device choice", "The physical device behind the DRM node, matched with " + c("VK_EXT_physical_device_drm") + ", never «the first card». One encode queue and one compute queue."],
        ["Discovery", c("vulkanvideo_capabilities()") + " opens and closes everything by itself: for H.264 High, HEVC Main and Main 10 it reports encoding yes/no, "
         "min and max size, rate-control modes, QP range, maximum level, DPB slots, input format, whether the shader can write the input image directly."],
        ["Latency", "Asks " + c("VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY_KHR") + "; if the driver refuses, retries with the default and records it (" + c("low_latency_requested") + ")."],
        ["Parameters", c("StdVideo*") + " structures with the same values " + c("vadirect.c") + " writes: High 8 bit or Main/Main 10, no B, one reference, BT.709 limited in the VUI. "
         + c("SLOT_DPB") + " = 2, " + c("INPUTS") + " = 2 input images in rotation, one slice per frame."],
        ["Headers", "Written by the driver from those parameters (" + c("vkGetEncodedVideoSessionParametersKHR") + "); if it changed something (" + c("hasOverrides") + ") the log says so. SPS, PPS and VPS go in front of every keyframe."],
        ["HEVC level fix", c("fix_hevc_level()") + " corrects the " + c("general_level_idc") + " byte in the returned VPS/SPS when the driver wrote the H.264 alphabet, walking the RBSP with its emulation bytes, and logs it."],
        ["Rate control", "CQP by default; with the ceiling VBR (average = working point, maximum = maximum rate, buffer in milliseconds from the VBV bits). Vulkan has no QVBR: the requested QP becomes the regulator's minimum QP (" + c("open_vulkan_card()") + ")."],
        ["Input, zero copy", "The DMA-BUF is imported (" + c("VK_EXT_external_memory_dma_buf") + ", " + c("VK_EXT_image_drm_format_modifier") + "), cached for up to " + c("IMPORTS_MAX") + " = 8 buffers and discarded when the producer's generation changes."],
        ["Input, memory", "The BGRx or RGBx pixels are uploaded as RGB and the same shader converts them."],
        ["Quality change", c("vulkanvideo_quality()") + " changes the QP (CQP) or the floor (VBR) live; it does not force a keyframe by itself."],
    ], "«TAB» — The Vulkan Video encoder") + \
    note("on the same machine, which card is used decides which route is taken: the virtual machines with the Radeon take Vulkan Video, the real "
         "machine with Intel graphics takes VA-API. Both routes have been seen working on Ubuntu 26.04, but on different benches; no machine with "
         "an AMD card was run through VA-API on Ubuntu 26.04 (forced with " + c("--encoding-route vaapi") + "): not verified. At startup of the "
         "virtual machines the service writes «THIS SERVER CANNOT ENCODE VIDEO … /dev/dri/renderD128 does not open» and about 2 s later «the card "
         "arrived 2 s after startup … HEVC: yes via vulkan · H.264: yes via vulkan»: the card's driver is still loading, and the retry "
         "described in " + rif("Codecs and their negotiation") + " closes it by itself.", "Which route the card takes.") + \
    p("<b>Cards that refuse linear buffers.</b> " + c("vulkanvideo_card_rejects_linear()") + " asks whether the card's GBM can create a LINEAR|RENDERING buffer; "
      "if not, " + c("vulkanvideo_modifiers()") + " lists the non-linear modifiers the card can import and sample, and the capture offers them (" + rif("Screen capture")
      + "). Intel and Radeon never take this branch.") + \
    p("<b>The bench switch.</b> " + c("REMOTIX_VULKAN_CONVERSION") + " set to " + c("copy") + " forces the shader to write into an intermediate image that is then "
      "copied, even where it could write the encoder's input directly. It exists to measure that branch; the product's choice is the one read from the driver. "
      "The shader's SPIR-V is a generated header, and the script that regenerates it (cited in the Makefile and in the shader's comment as "
      "benches/19-vulkan/19-shader.sh) is not part of this tree.")

# ── 8 ───────────────────────────────────────────────────────────────────────
S8 = p("The capture delivers RGB and the encoders want YUV 4:2:0. The conversion is always <b>BT.709, from full-range RGB to limited-range YUV</b> "
       "(Y 16 to 235, Cb and Cr 16 to 240; at 10 bits 64 to 940 and 64 to 960), and the stream's VUI says so. Who converts depends on the route.",
       lead=True) + \
    table(["Route", "Converter", "Notes"], [
        ["VA-API, zero copy", "The GPU's video processor (VPP, " + c("VAEntrypointVideoProc") + "), " + c("convert_on_gpu()"),
         "Matrix imposed: source " + c("VAProcColorStandardNone") + " full range, output " + c("VAProcColorStandardBT709") + " reduced range; regions declared"],
        ["VA-API, from memory", c("colors709.c") + " in CPU into NV12/P010, then " + c("vadirect_load_nv12()") + " or " + c("vadirect_load_p010()"), "Uploading RGB for the VPP was found worse (comment of " + c("vadirect.c") + ")"],
        ["Vulkan, both inputs", c("vulkanvideo_rgb_nv12.comp") + " on the compute queue", "Same integer arithmetic as " + c("colors709.c") + ", the same bytes"],
    ], "«TAB» — Who converts the colours") + \
    p("<b>The arithmetic</b> (" + c("colors709.c") + " and the shader): coefficients in fixed point with " + c("SCALE") + " = 15 fractional bits so each fits an "
      + c("int16") + " for " + c("pmaddwd") + "; luma (" + c("YR") + " 5983, " + c("YG") + " 20127, " + c("YB") + " 2032) sums to 28142 = 219/255 · 32768, so white gives "
      "235 and black 16; Cb (−3298, −11094, 14392) and Cr (14392, −13072, −1320) each sum to 0, so every grey is exactly 128. Chroma is the sum of each "
      "horizontal pair, filtered vertically with a 1-3-3-1 tent over four rows, rounded to nearest. At 10 bits the matrix is computed at 10 bits and P010 "
      "stores the ten bits high in sixteen. x86-64 always has SSE2, so there is no runtime dispatch (" + c("COLORS709_SSE2") + "); other architectures run the same arithmetic "
      "in plain C with the same bytes.") + \
    warn("leaving the VPP regions NULL means «the whole surface», and the destination surface is aligned (1920×1088 on iHD for 1080p): the VPP would then "
         "<i>scale</i> 1080 rows to 1088, a slightly blurred, slightly stretched desktop with no log line. Both regions are the canvas, and the source is the canvas size "
         "(comment in " + c("encoder.c") + ").", "The 1088-row scaling.") + \
    note("the comments record that the Radeon's VPP loses on chroma against the CPU reference; with Vulkan on AMD the shader does the conversion instead.", "Radeon VPP.") + \
    note("the stream of Mutter 50 declares " + c("colorPrimaries") + " = BT709 and " + c("transferFunction") + " = GAMMA22 and Mutter composes SDR with "
         "gamma 2.2 (read in the source, " + rif("PipeWire negotiation, resize and wake-up") + "). " + c("colors709.c") + " and the shader use the BT.709 matrix and ignore "
         "the transfer tag, as before. Whether the result differs visibly from Debian was not compared: not verified.", "Gamma 2.2 on GNOME 50.")

# ── 9 ───────────────────────────────────────────────────────────────────────
S9 = p(c("bit_writer.c") + " knows no codec: it knows bits, Exp-Golomb and the " + c("00 00 03") + " rule. Which fields to write and in which order is in "
       + c("vadirect.c") + ", with the standard's clause beside each line. It is the mirror of the " + c("BitReader") + " in " + c("encoder.c") + ", which reads back "
       "what was produced.", lead=True) + \
    table(["Function", "Writes"], [
        [c("bw_u()"), "The " + c("n") + " low bits of " + c("v") + ", most significant first (n up to 32)"],
        [c("bw_flag()"), "One bit"],
        [c("bw_ue()") + " / " + c("bw_se()"), "Unsigned and signed Exp-Golomb"],
        [c("bw_close_rbsp()"), "The RBSP trailing bits: a 1 then zeros to the byte"],
        [c("bw_align_with_uni()"), "Ones to the byte (the tail of an H.264 slice header under CABAC)"],
        [c("bw_copy_bit()"), "Copies a run of bits from a source: used to rewrite the head of an SPS and copy the tail as is"],
        [c("nal_annexb()"), c("00 00 00 01") + ", the NAL header unchanged, then the RBSP with emulation prevention; 0 if the output is too small"],
    ], "«TAB» — The bit writer") + \
    p("A field that does not fit sets " + c("overflowed") + " and whoever closes the NAL sees it: a truncated header looks like a header.") + \
    h4("The cropping window rewrite") + \
    p("The comments record that on a Radeon with Mesa radeonsi, HEVC at 2544×1344 produced a stream <i>declaring</i> 2560×1344: the card codes the multiple of "
      "its 64-pixel block and does not write the conformance window. The byte check rightly refuses a stream whose size differs from the canvas, so the "
      "session would stay black. " + c("border_in_place()") + " decides on the first SPS of each encoder context: if the stream is larger than the canvas by less than 64 "
      "pixels on each side and by even amounts, the window is written. " + c("rewrite_sps_with_crop()") + " re-reads the SPS up to the cropping flag, rewrites the head "
      "identically, sets the flag with the four offsets (in chroma units), copies the tail bit by bit to the stop bit, and puts the NAL back with its emulation "
      "bytes. Only keyframes carry an SPS, so only they are touched; any other mismatch remains an error.")

# ── 10 ──────────────────────────────────────────────────────────────────────
S10 = p("Pure Annex-B and no " + c("description") + ". Every keyframe carries its parameter sets in front (H.264: SPS, PPS, IDR; HEVC: VPS, SPS, PPS, IDR), so a "
        "client that attaches late decodes from the first key it sees. The stream is described in " + rif("The RCP/1 protocol") + ".", lead=True) + \
    p("Before any byte leaves, " + c("bitstream_ok()") + " checks it, because a decoder fed the wrong shape does not complain: it paints black, or at the old size.") + \
    ul(["the frame starts with a start code (not a length prefix);",
        "a keyframe has its parameter sets before the IDR;",
        "the SPS is read with the bit reader (" + c("read_h264_sps()") + ", " + c("read_hevc_sps()") + "), and the depth and the displayed size in the bytes must equal what was "
        "requested; the size coded and the size displayed are kept apart (" + c("encoded_width") + " and " + c("stream_width") + ": on radeonsi 1080p is coded as 1088 and cropped);",
        "a frame larger than " + c("FRAME_CAP") + " (16 MiB) is never sent."]) + \
    p("<b>The confession.</b> " + c("codificatore_confessione()") + " returns what the encoder actually did, from two independent witnesses: the context (component opened, "
      "route, vendor, entry point verified, size limits, rate-control mask and mode read back, working point, maximum rate, VBV) and the bytes (depth, profile, level, tier, "
      "sizes, chroma format, " + c("codec_string") + "). If they disagree the component disobeyed: " + c("has_obeyed") + " becomes false (the reason is in " + c("why_no") + ") and nothing is sent.") + \
    table(["Codec", "Field in the SPS", "Level 5.1 is written as"], [
        ["H.264", c("level_idc") + " = major·10 + minor", "51"],
        ["HEVC", c("general_level_idc") + " = (major·10 + minor)·3", "153"],
        ["AV1 (reserved)", c("seq_level_idx") + " = (major − 2)·4 + minor", "13"],
    ], "«TAB» — Three alphabets for one level (" + c("level_in_tenths()") + " in child.c translates back)") + \
    p("<b>The level is imposed, then verified.</b> RCP/1 says the server must not emit a level above the client's " + c("video.level") + ", and the browser does not "
      "enforce it, so the check is the server's. " + c("imposed_level()") + " translates the ceiling into the codec's alphabet, the encoder writes it, and the child logs "
      "the level read from the bytes in decimal next to the client's. The declared cost: a level's frame-rate limit can be exceeded, because the encoder keeps running "
      "at " + c("MOTION_FPS") + " = 60; halving the rate would change what the user sees and is not done. The largest canvas, 4096×2304, is exactly the " + c("MaxFS") + " of H.264 levels 5.1 and 5.2 (36864 macroblocks); for HEVC it is above the picture size of level 5.1 in the encoder's own table (8 912 896 samples), and the imposed level is written all the same.") + \
    p("A change of negotiated depth, level ceiling or capture channel order (BGRx and RGBx) between two clients of the same session rebuilds the encoder, because "
      "these are fixed at opening; the next frame is a key.")

# ── 11 ──────────────────────────────────────────────────────────────────────
S11 = p("The GOP is infinite (" + c("chiavi_ogni") + " = 0): periodic keyframes are bandwidth spent on an insurance the protocol already buys, and on a bad line keys "
        "sent by the clock are the spiral RCP/1 forbids. A keyframe is produced exactly when one is owed.", lead=True) + \
    table(["Cause", "How"], [
        ["First frame after " + c("SESSION"), "A new encoder has no past; its first frame is an IDR"],
        ["First frame at a new canvas", c("codificatore_ridimensiona()") + " closes and reopens the context"],
        ["The client asks", c("REQUEST_KEY") + " reaches the child as a video message with " + c("key = 1") + ", sets " + c("key_debt") + ", and the child calls "
         + c("codificatore_chiedi_chiave()") + " before compressing"],
        ["A delta was abandoned", "RCP/1: the server must send a key as soon as it can, without waiting to be asked (" + rif("Quality, degradation and budget") + ")"],
        ["The encoder was rebuilt", "Depth, level or channel order changed; or a quality step reopened the context"],
    ], "«TAB» — When a keyframe is produced") + \
    p("A keyframe on a still desktop has nothing to encode, because the compositor sends nothing: the child wakes the stream so a frame arrives (" + rif("Screen capture") + ").")

S12 = p(c("codificatore_ridimensiona()") + " reopens the encoder at the new size; the first frame after is a true key. The size it receives has already been checked by "
        + c("rcp_size_allowed()") + ": at least " + c("RCP_CANVAS_MIN_W") + "×" + c("RCP_CANVAS_MIN_H") + " (320×240), at most " + c("RCP_CANVAS_MAX_W") + "×" + c("RCP_CANVAS_MAX_H")
        + " (4096×2304; the declared limit of the product is 3K), even sides; a larger request is <i>reduced</i> (the side that overflows goes to the maximum, the other stays), a smaller one is refused. The driver's own "
        "maximum is still read at every opening (" + c("max_size_w") + ", " + c("max_size_h") + "), and " + c("vulkan_fit()") + " compares the canvas with the card's limits.", lead=True) + \
    p("<b>The frame ceiling.</b> " + c("FRAME_CAP") + " is 16 × 1024 × 1024 bytes. A frame that exceeds it is re-encoded at lower quality and never sent; the ladder "
      "(" + c("lower_quality()") + ", " + c("CRF_STEP") + " = 9, " + c("MAX_REENCODES") + " = 3) and its way back are in " + rif("Quality, degradation and budget") + ".") + \
    p("Encoding at a size that is not a multiple of the block: H.264 writes the cropping window itself; HEVC relies on the driver and, where the driver does not write "
      "it, on the rewrite of the previous section. With Vulkan the capture slabs on labwc stay at the maximum canvas across resizes (" + rif("Screen capture") + ").")

# ── 13 ──────────────────────────────────────────────────────────────────────
S13 = p("Every encoded frame carries its costs separately, so that a drop in frame rate can be attributed. They are logged for the first frame and summarised afterwards; "
        "performance figures with their hardware are in " + rif("Performance and capacity") + ".", lead=True) + \
    table(["Field of " + c("EncoderFrame"), "What it measures"], [
        [c("us_conversione"), "RGB to YUV: the VPP or the shader on the GPU, or " + c("colors709.c") + " in CPU"],
        [c("upload_us"), "Memory to GPU upload; <b>0 on zero copy</b>, where the stretch does not exist"],
        [c("us_codifica"), "From handing the input to the encoder to the bytes read back"],
        [c("reencodes"), "Re-encodings forced by the 16 MiB ceiling (above 0 means it bit)"],
        [c("trattenuto"), "The encoder did not deliver the frame at once (one frame of delay)"],
        [c("key"), "Keyframe (RCP/1 type " + c("0x0301") + ") or delta (" + c("0x0302") + ")"],
    ], "«TAB» — The timings of one frame") + \
    table(["Constant", "Value", "File"], [
        [c("RENDER_NODE"), c("/dev/dri/renderD128"), c("child.c")],
        [c("RENDER_POWER"), c("ENCODER_POWER_DECLARED"), c("child.c")],
        [c("QP_HARDWARE"), "26", c("child.c")],
        [c("CODEC_MAX"), "4 (index by codec number)", c("child.c")],
        [c("PROBE_SIDE") + " / " + c("PROBE_ROUNDS"), "256 px / 8 attempts", c("child.c")],
        [c("ENC_RETRY_MIN_MS") + " / " + c("ENC_RETRY_MAX_MS"), "500 ms / 10 s", c("child.c")],
        [c("FRAME_CAP"), "16 MiB", c("encoder.c")],
        [c("CARD_ALIGNMENT"), "64 bytes (DMA-BUF stride)", c("encoder.c")],
        [c("IMPORTED_MAX") + " / " + c("READY_SURFACES"), "8 / 4", c("encoder.c")],
        [c("BANDWIDTH_WINDOW_US"), "10 s", c("encoder.c")],
        [c("REBUILT") + " / " + c("CODED_MARGIN"), "3 / 64 KiB", c("vadirect.c")],
        [c("SLOT_DPB") + " / " + c("INPUTS") + " / " + c("IMPORTS_MAX"), "2 / 2 / 8", c("vulkanvideo.c")],
    ], "«TAB» — Encoder constants") + \
    tip("the log area of the encoder is " + c("video") + "; the line that starts with " + c("opened:") + " names the codec, depth, component, node, vendor and (on VA-API) "
        "the entry point actually in force. " + c("remotix --encoding-test") + " with " + c("--encoding-route vulkan") + " or " + c("--encoding-route vaapi") + " reproduces one route in isolation.",
        "Diagnosis.") + \
    h4("What was verified, and what was not") + \
    ul(["<b>Verified (Ubuntu 26.04):</b> the four desktops with real browsers through " + c("prove/all.sh") + ", and in particular " + c("prove/check-media.py")
        + " «codec» (the line " + c("media/codec") + " is green in the round of 26-27 Nov 2026 on the four virtual machines; Chrome 156 and Firefox 153.7 negotiate H.264 " + c("avc1.640033") + " at 8 bits on the test machines), "
        "which reads from the journal which codec, level and GPU node the server negotiated and that the picture is sharp at the default quality; on the "
        "virtual machines with the Radeon, the " + c("opened:") + " lines of the encoding test for HEVC and H.264 via Vulkan Video; on the real Kubuntu live image "
        "with Intel graphics, HEVC via VA-API; installation, remove and purge in the test machines (the package check " + c("check-package.py") + " does not run in the "
        "virtual-machine bench, which skips it).",
        "<b>Known behaviour without a card:</b> on the virtual machines, at service start, the card's driver is still loading and the log says the server cannot encode video; about 2 s later the retry of " + c("rootside.c") + " finds the card (" + rif("Codecs and their negotiation") + "). A machine with no card at all was not run on Ubuntu; the Debian notes recorded the error repeating every 2 s, which loop writes it was not traced.",
        "<b>Not verified:</b> NVIDIA on this tree (measured on Ubuntu 26.04 on 5–6 Oct 2026, with an earlier version of the code); the VA-API route on an AMD card on Ubuntu; a "
        "virtual machine with no video card at all (the refusal at installation is in the package scripts, not exercised on Ubuntu here); a canvas at 4096×2304 end to end (the test "
        "browser's decoder stops at 3840×2160); AV1 (not offered); the padding layers' effect by eye on AMD in this build; the render group and ACL grant on machines with "
        "lingering users on Ubuntu."])

CHAPTER = ("Video encoding", [
    ("Encoding at a glance: one front, two GPU routes", S1),
    ("Codecs and their negotiation", S2),
    ("Choosing the GPU route", S3),
    ("Choosing the card and granting access to it", S4),
    ("The encoding test: remotix --encoding-test", S5),
    ("VA-API without libavcodec", S6),
    ("The Vulkan Video encoder", S7),
    ("BT.709 colour conversion", S8),
    ("Writing the bitstream headers", S9),
    ("Bytes, levels and the confession", S10),
    ("Keyframes on demand", S11),
    ("Resizing the encoder and the frame ceiling", S12),
    ("Encoder timings, constants and verification status", S13),
])
