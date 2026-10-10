from build import arrow, box, c, code, fig, flow, h4, note, p, rif, table, text, tip, ul, warn, zone

# ── 7.1 ─────────────────────────────────────────────────────────────────────
VIA = fig(
    box(20, 30, 160, 64, "Captured frame", "DMA-BUF or pixels", "navy")
    + box(220, 30, 200, 64, "codificatore.c", "one front for two paths", "blue")
    + box(470, 8, 190, 56, "vulkanvideo.c", "Vulkan Video (AMD, NVIDIA)", "light")
    + box(470, 74, 190, 56, "vadiretta.c", "VA-API via libva (Intel)", "light")
    + box(700, 30, 180, 64, "Annex-B bytes", "checked, then sent", "green")
    + arrow(182, 62, 218, 62) + arrow(422, 52, 468, 36) + arrow(422, 72, 468, 102)
    + arrow(662, 36, 698, 56) + arrow(662, 102, 698, 70)
    + box(220, 150, 200, 50, "colori709.c", "BT.709 in CPU, memory path", "grey")
    + box(470, 150, 190, 50, "shader .comp", "BT.709 on the GPU", "grey")
    + box(700, 150, 180, 50, "scrittore_bit.c", "SPS/PPS/VPS bits", "grey")
    + arrow(320, 148, 320, 96, "#475569", True) + arrow(565, 148, 565, 132, "#475569", True)
    + arrow(790, 148, 610, 116, "#475569", True)
    + text(450, 228, "No ffmpeg, no CPU encoder: without a capable GPU the server offers no codec", 11, "#475569"),
    900, 236, "«FIG» — The encoder: one front, two GPU paths chosen by capability, three helpers")

S1 = p("REMOTIX encodes every frame on the GPU, in H.264 or HEVC, into Annex-B that the browser's WebCodecs "
       + c("VideoDecoder") + " decodes. " + c("codificatore.c") + " (the encoder) is the front: it chooses the GPU path by "
       "capability — Vulkan Video if the card encodes that codec through Vulkan, VA-API otherwise — and keeps "
       "everything that works on the bytes (shape checks, keyframes, the 16 MiB ceiling, quality steps, the "
       "level check) in one place for both paths. ffmpeg left the product in phase 18 and the software "
       "encoders in phase 19: a server without a capable GPU says so at startup and offers no video codec.",
       lead=True) + VIA + \
    table(["File", "Role"], [
        [c("codificatore.c") + " / " + c("codificatore.h"), "Opens the encoder by name, chooses the path, "
         "converts or imports the input, checks the bytes, keeps the confession, keyframes, ceiling, resize"],
        [c("vulkanvideo.c") + " / " + c("vulkanvideo.h"), "Vulkan Video: discovery per DRM node, session, "
         "parameters, DMA-BUF import, colour conversion shader, the encode loop"],
        [c("vulkanvideo_rgb_nv12.comp"), "Compute shader RGB → NV12/P010, BT.709 limited; compiled into "
         + c("vulkanvideo_rgb_nv12_spv.h") + ", which is kept in the repository so the product needs no shader "
         "compiler"],
        [c("vadiretta.c") + " / " + c("vadiretta.h") + " (direct VA-API)", "libva used directly: configuration, sequence/picture/slice "
         "parameters, packed headers, begin/render/end, the coded buffer"],
        [c("colori709.c") + " / " + c("colori709.h"), "BGRx/RGBx → YUV 4:2:0 BT.709 limited in CPU (SSE2), for "
         "the VA-API memory path"],
        [c("scrittore_bit.c") + " / " + c("scrittore_bit.h"), "Bit writer: " + c("u(n)") + ", " + c("ue(v)")
         + ", " + c("se(v)") + ", trailing bits, NAL units with emulation prevention"],
        [c("figlio.c") + " (the per-user child)", "Asks for the encoder (" + c("codificatore_di()") + "), feeds it, probes the GPU at "
         "startup (" + c("figlio_capacita_video()") + ") and for the installer (" + c("--prova-codifica") + ", the encoding probe)"],
    ], "«TAB» — The files of the encoder")

# ── 7.2 ─────────────────────────────────────────────────────────────────────
S2 = p("RCP/1 numbers the video codecs in the frame header: <b>1 = HEVC, 2 = AV1, 3 = H.264</b>. The enum "
       + c("CodecVideo") + " uses the same values so that no conversion table can drift. AV1 is no longer "
       "negotiated, but its number is reserved forever: an old client hearing “2” and receiving H.264 would "
       "paint garbage without an error.", lead=True) + \
    table(["Date", "Decision", "What drove it"], [
        ["12 Aug 2026", "HEVC first, AV1 as negotiated fallback (" + c("DECISIONI.md") + " §1.13)",
         "Measured in browsers: HEVC Main10 painted only in Chrome with GPU decoding (8 cells of 8), never in "
         "Firefox or in Chrome without GPU; AV1 painted everywhere, even in software"],
        ["13 Aug 2026", "Encoding on the GPU brought forward to phase 3", "HEVC on VA-API cost 3.16–3.24 ms per "
         "1920×1080 frame against tens of ms in software; " + c("av1_vaapi") + " exited with «No usable encoding "
         "profile found» and " + c("vainfo") + " listed AV1 for decoding only on both cards"],
        ["17–20 Aug 2026", "AV1 out, H.264 in (§1.13-ter: the user's decision of 17 Aug, implemented 20 Aug)", "Firefox for Android had neither HEVC "
         "nor AV1; H.264 was the only codec in hardware at both ends (3.11 ms on the server, hardware decoding on "
         "the tablet); and Firefox painted rectangular blocks with AV1 where Chrome and dav1d were clean on the "
         "same bytes"],
        ["30 Sep 2026", "H.264 stays (§10.26)", "The Android reason had fallen (Firefox for Android has no WebCodecs "
         "at all and is unsupported, §7.18), but Firefox on Linux does not decode HEVC and works in H.264"],
        ["1 Oct 2026", "No CPU encoding (§10.27)", "The user: the GPU is always used, NVIDIA included; without a "
         "capable card REMOTIX does not encode"],
    ], "«TAB» — How the codec set came to be") + \
    p("<b>What the server offers is measured, not written.</b> At startup " + c("main.c") + " calls "
      + c("figlio_capacita_video()") + ", which forks a short-lived process (a driver that crashes must not take "
      "the server with it before it has opened its port) that opens each codec through the same "
      + c("codificatore_di()") + " a session uses and encodes a 256×256 test frame until bytes come out "
      "(at most 8 attempts). The result is passed to " + c("rcp_video_codec_imposta()") + ": "
      + c("hevc,h264") + ", " + c("hevc") + ", " + c("h264") + " or empty. With an empty list every "
      + c("CIAO") + " ends in " + c("NIENTE_IN_COMUNE") + " and the startup log says why, with the remedy. A "
      "browser must never be offered a codec the server cannot keep: negotiating HEVC and then failing to open "
      "it was a black screen with no line naming it.") + \
    table(["Capability", "Page (" + c("pagina.html") + ")", "Server (" + c("rcp.c") + ")"], [
        [c("video.codec"), "Probed by decoding: " + c("PREFERENZA") + " (preference) = " + c("[\"hevc\", \"h264\"]")
         + ", filtered to the codecs that reach the pixel in this browser", "The measured list; the "
         "negotiated codec is the first entry of the <b>browser's</b> list that the server also offers ("
         + c("prima_comune()") + ")"],
        [c("video.profondita"), "The depths that painted, in the order 8, 10", c("8,10") + "; the client must "
         "include 8. With this page the result is 8"],
        [c("video.livello"), c("LIVELLO_DICHIARATO") + " (declared level) = " + c("5.1"), "A ceiling the encoder must respect ("
         + rif("Bytes, levels and the confession") + ")"],
    ], "«TAB» — The video capabilities exchanged in the handshake") + \
    p("The codec string the page passes to " + c("VideoDecoder.configure()") + " is built by "
      + c("stringhe_codec()") + ": for H.264 " + c("avc1.6400") + " plus the level in <i>hexadecimal</i> "
      "(5.1 → " + c("avc1.640033") + "; decimal would give the invalid " + c("avc1.100051") + "), with "
      + c("avc1.64001f") + " (level 3.1) as second choice; for HEVC " + c("hev1.1.6.L<level·30>.B0")
      + " (Main) or " + c("hev1.2.4…") + " (Main 10), with " + c("L93") + " as second choice. The server composes "
      "its own string from the SPS it produced (" + c("stringa_codec") + " in the confession): since phase 18 "
      "the H.264 SPS sets constraint flags 4 and 5 (High, no B frames), so the server reads for example "
      + c("avc1.640c15") + " (the 256×256 probe, level 2.1); the profile and level bytes are what decoders "
      "use.") + \
    note("the H.264 encoder is <b>High, 8 bit</b> only. " + c("profilo_va()") + " returns " + c("VAProfileNone")
         + " for H.264 at 10 bits instead of trying (" + c("vainfo") + " on the test server lists "
         + c("VAProfileH264High") + " only), and the Vulkan path refuses it in " + c("vulkan_adatta()")
         + ". HEVC is Main or Main 10. The capture is 8 bits per channel on every desktop, so a 10-bit stream "
         "would be 8 bits promoted; the confession declares it (" + c("promozione_8_a_10") + ").", "Depth.")

# ── 7.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The encoder is asked for <b>by name</b>, and the name says how the path is chosen. A name that is not "
       "one of these six is refused by " + c("codificatore_nuovo()") + " with the reason; there is no silent "
       "fallback to another component, profile or depth, because two measurements under one label are worse "
       "than none.", lead=True) + \
    table(["Name", "Path", "Used by"], [
        [c("h264_scheda") + ", " + c("hevc_scheda") + " (" + c("scheda") + " = card)", "By capability: Vulkan Video if " + c("vulkan_adatta()")
         + " says the card fits this request, otherwise VA-API (and the log says why)", "The product (default)"],
        [c("h264_vulkan") + ", " + c("hevc_vulkan"), "Vulkan only; failure if unavailable",
         c("--codifica vulkan") + ", benches, diagnosis"],
        [c("h264_vaapi") + ", " + c("hevc_vaapi"), "VA-API only (" + c("vadiretta.c") + ")",
         c("--codifica vaapi") + ", the phase 18/19 benches"],
    ], "«TAB» — The six component names") + \
    p(c("figlio.c") + " builds the name from the codec and the path in force (" + c("componente_di()")
      + "); the path is " + c("scheda") + " (by capability) unless the server was started with " + c("--codifica scheda|vulkan|vaapi")
      + ", which the parent repeats on every child's command line (the child is an " + c("exec") + ", a static "
      "of the parent would not reach it). The name actually opened — " + c("h264_vulkan") + " or "
      + c("h264_vaapi") + " — is what " + c("codificatore_nome()") + " and the log report, together with the node, "
      "the vendor string and the entry point.") + \
    table(["Condition checked by " + c("vulkan_adatta()"), "If it fails"], [
        ["Input is RGB (not the bench's " + c("yuv420p10le") + ")", "VA-API"],
        ["H.264 at 8 bits; codec is H.264 or HEVC", "VA-API"],
        [c("vulkanvideo_capacita()") + " finds a Vulkan device with an encode queue on the node", "VA-API"],
        ["The profile (H.264 High, HEVC Main, HEVC Main 10) declares encoding", "VA-API"],
        ["The canvas is within the card's minimum and maximum size", "VA-API"],
        ["The rate-control mode needed is declared: CQP without the bandwidth ceiling, VBR with it", "VA-API"],
        ["The current QP is within the card's QP range", "VA-API"],
    ], "«TAB» — When Vulkan Video is taken") + \
    p("<b>The node is declared, not guessed.</b> " + c("NODO_RENDERING") + " is " + c("/dev/dri/renderD128")
      + ", fixed in " + c("figlio.c") + "; no environment variable moves it (a node from a variable would vanish "
      "the day someone started the service by hand, and the symptom would be a different encoder under the same "
      "label). Only " + c("--prova-codifica --nodo …") + " uses another node, to test a second card. On the test "
      "server the two nodes are two vendors: " + c("renderD128") + " the Intel iGPU (iHD, "
      + c("VAEntrypointEncSliceLP") + "), " + c("renderD129") + " a Radeon RX 6800 (radeonsi, "
      + c("VAEntrypointEncSlice") + "). Measured 13 Aug 2026 at 1920×1080: Intel 3.16–3.24 ms, Radeon 3.43 ms "
      "per frame.") + \
    p("<b>The VA-API entry point</b> is a declared rule, " + c("CODIFICATORE_POTENZA_LA_DICHIARATA") + ": "
      "low-power " + c("EncSliceLP") + " if the driver declares it for the profile, full " + c("EncSlice")
      + " otherwise, failure if neither. The pair is read with " + c("vaQueryConfigEntrypoints()") + " before "
      "opening (three outcomes: present, absent, could not look). On the Radeon only " + c("EncSlice")
      + " exists, and with the old fixed low-power request sessions fell back to software. Before opening the "
      "driver is also asked for the maximum size (" + c("vaGetConfigAttributes()") + "; H.264 on Intel "
      + c("EncSliceLP") + " accepts 32–4096 px per side, measured 22 Aug 2026) and the rate-control modes.") + \
    p("<b>When opening fails</b> the child does not retry at every frame: the wait doubles from "
      + c("CODIF_RIPROVA_MIN_MS") + " = 500 ms to " + c("CODIF_RIPROVA_MAX_MS") + " = 10 s, and the log says the "
      "next attempt time (retrying freely once wrote 30.8 GB of log in minutes, 14 Aug 2026). A full card is not "
      "a missing codec: on an RTX 4090 (driver 595, 6 Oct 2026) the driver gives 12 encode sessions for the "
      "whole card, the thirteenth " + c("vkCreateVideoSessionKHR") + " returns " + c("VK_ERROR_TOO_MANY_OBJECTS")
      + ", and the log says “the card is there but has run out of encode slots”; the session gets its first "
      "frame by itself when a slot frees.") + \
    h4("The certification probe: remotix --prova-codifica") + \
    p("The installer asks the product itself whether this machine encodes a frame on the GPU. "
      + c("remotix --prova-codifica [h264|hevc] [--nodo /dev/dri/…] [--codifica vaapi|vulkan|scheda]")
      + " goes through " + c("codificatore_di()") + " (H.264, 8 bits, no level ceiling, BGRx), encodes a "
      "256×256 frame until bytes come out, and prints one JSON line on stdout (the log goes to stderr):") + \
    code('{"esito":"hardware","codificatore":"h264_vaapi","strada":"vaapi","nodo":"/dev/dri/renderD128",\n'
         ' "motivo":"…","codec":"h264","offerti":"hevc,h264","hevc":"hardware","h264":"hardware",\n'
         ' "hevc_strada":"vaapi","h264_strada":"vaapi"}', "text", "The probe's answer (shape)") + \
    p(c("esito") + " (outcome) is " + c("hardware") + " or " + c("nessuno") + " (none); " + c("strada") + " is the path "
      "that encoded; " + c("offerti") + " (offered) is what the server would offer the browser with the same arguments; "
      + c("hevc") + "/" + c("h264") + " and " + c("hevc_strada") + "/" + c("h264_strada") + " give the same answer per codec. "
      "The installer reads " + c("esito") + " and the exit code.") + \
    table(["Exit code", "Meaning"], [
        ["0", "The GPU encoded a frame and the bytes were read back"],
        ["1", "The GPU opens but no frame came out, or it cannot be told whether it is right"],
        ["2", "Usage error"],
        ["3", "No GPU can encode this codec (no node, no driver, a driver without encoding)"],
    ], "«TAB» — Exit codes of --prova-codifica") + \
    p("“hardware” is said only if the component accepts GPU surfaces, a frame came out with bytes, and the bytes "
      "were read back (" + c("letto_dal_flusso") + ", read from the stream). Permissions matter: without the node's group "
      "(" + c("render") + ") a user sees " + c("nessuno") + " (none) where root would see " + c("hardware") + ", so the probe must run with the "
      "identity in question. How the installer uses it is in " + rif("The installer") + ".")

# ── 7.4 ─────────────────────────────────────────────────────────────────────
S4 = p("Until phase 18 the VA-API path was libavcodec's " + c("h264_vaapi") + " and " + c("hevc_vaapi")
       + ". " + c("vadiretta.c") + " talks to libva (MIT) directly and does the four things they did: "
       "configure the driver, fill the sequence/picture/slice parameters, write the stream headers, and run "
       "begin/render/end for each frame. Its governing rule is to reproduce exactly what ffmpeg 7.1 did, field "
       "by field, so that the browser receives the same kind of stream.", lead=True) + \
    table(["Choice", "Value", "Why"], [
        ["GOP", c("intra_period = intra_idr_period = INT_MAX") + " when " + c("chiavi_ogni") + " (keyframe interval) = 0",
         "Keyframes only on request (" + rif("Keyframes on demand") + ")"],
        ["B frames", "None: " + c("ip_period = 1"), "Latency weighs more than compression: a frame waiting for the "
         "next one is a frame of delay"],
        ["References", "1 (" + c("max_num_ref_frames") + "), " + c("RICOSTRUITE") + " = 3 reconstructed surfaces",
         "Current and reference, one turn of margin"],
        ["H.264 SPS", "High (100), constraint_set4 = 1, constraint_set5 = 1, POC type 2, 8-bit "
         + c("frame_num") + ", cropping when the canvas is not a multiple of 16",
         "As ffmpeg wrote it for a stream without B frames"],
        ["VUI", "Video signal type present, limited range, primaries/transfer/matrix = 1 (BT.709), timing "
         "(time_scale = 2·fps), bitstream restriction (" + c("max_num_reorder_frames = 0") + ")",
         "Firefox ignores full range, measured; the colour must be declared, not assumed"],
        ["HRD", "Only with the bandwidth ceiling (QVBR); never " + c("cbr_flag"), "Matches ffmpeg"],
        ["Rate control", c("VA_RC_CQP") + " (QP 26) by default; " + c("VA_RC_QVBR") + " with the ceiling",
         "Asked by name and verified against the driver's mask (" + rif("Quality, degradation and budget") + ")"],
        ["Level", "Computed as ffmpeg did (" + c("ff_h264_guess_level") + " logic) or imposed from "
         + c("video.livello"), "The client's level is a must"],
        ["Coded buffer", "3 × aligned surface width × height + 64 KiB (" + c("CODED_MARGINE") + ")", "ffmpeg's rule: an "
         "uncompressed frame bounds a compressed one"],
        ["Synchronisation", "Each frame waits for the GPU (" + c("vaSyncBuffer") + " or " + c("vaSyncSurface")
         + ")", "There is no " + c("async_depth") + " any more: libavcodec's default of 2 was never asked for"],
        ["SEI", "An identification SEI with REMOTIX's UUID on the first frame (ffmpeg wrote its own)",
         "The page reads only SPS and PPS"],
    ], "«TAB» — The VA-API stream, as vadiretta.c writes it") + \
    p("Headers are passed to the driver as <i>packed headers</i>; " + c("VaDirettaDichiarazione")
      + " records the mask the driver declares and the one in force, the surface alignment (16 for H.264, the "
      "CTB for HEVC), whether HEVC P frames are coded as generalised-B slices (" + c("p_come_b") + ", iHD) and "
      "the input fourcc (" + c("NV12") + " or " + c("P010") + ").") + \
    note("on Mesa radeonsi the driver reads REMOTIX's packed headers and regenerates them (measured 30 Sep 2026: "
         + c("log2_max_mv_length 16") + ", " + c("transform_8x8 0") + " in H.264; a VPS without timing, "
         + c("temporal_mvp 0") + ", " + c("cabac_init_present 1") + " in HEVC). It did the same to ffmpeg, so "
         "the stream is unchanged. For the same reason the cropping window that Mesa 25.0.7 does not write is "
         "fixed afterwards on the bytes (" + rif("Bytes, levels and the confession") + ").", "Radeon rewrites "
         "the headers.")

# ── 7.5 ─────────────────────────────────────────────────────────────────────
S5 = p("Vulkan Video is the path the user asked for first (1 Oct 2026: “with standard tools, preferably Vulkan, "
       "which all four architectures share”): the NVIDIA proprietary driver does not encode through VA-API, but "
       "every vendor exposes Vulkan Video. " + c("vulkanvideo.c") + " uses " + c("VK_KHR_video_encode_queue")
       + " with " + c("VK_KHR_video_encode_h264") + "/" + c("_h265") + ", the Vulkan loader (Apache-2.0) and the "
       "system driver; nothing else.", lead=True) + \
    table(["Vendor (as of Oct 2026)", "Path", "Evidence"], [
        ["AMD with RADV", "Vulkan", "Measured 1 Oct 2026, Mesa 25.0.7, RX 6800: H.264 and HEVC"],
        ["NVIDIA, proprietary driver", "Vulkan", "Measured 5–7 Oct 2026, RTX 4090, driver 595.91.07, Ubuntu 26.04: "
         + c("h264_vulkan") + ", " + c("hevc_vulkan") + "; certified on Ubuntu 26.04 only"],
        ["Intel (integrated, Arc)", "VA-API", "ANV encodes only behind " + c("ANV_DEBUG=video-encode")
         + " (Mesa 25.0.7 and 26.2.3, 1 Oct 2026): experimental, not used"],
    ], "«TAB» — Which cards take which path") + \
    table(["Aspect", "What vulkanvideo.c does"], [
        ["Device choice", "The physical device behind the DRM node, matched with "
         + c("VK_EXT_physical_device_drm") + " — never “the first card”. One encode queue and one compute queue."],
        ["Discovery", c("vulkanvideo_capacita()") + " opens and closes everything by itself: for H.264 High, HEVC "
         "Main and Main 10 it reports encoding yes/no, min/max size, rate-control modes, QP range, maximum level, "
         "DPB slots, input format, whether the shader can write the input image directly. The installer's "
         "preflight uses the same discovery."],
        ["Latency", "Asks " + c("VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY_KHR") + "; if the driver refuses, "
         "retries with the default and records it (" + c("ritardo_minimo_chiesto") + ", minimum latency requested)."],
        ["Parameters", c("StdVideo*") + " with the same values " + c("vadiretta.c") + " writes: High 8 bit or "
         "Main/Main 10, no B, one reference, BT.709 limited in the VUI, level computed like ffmpeg or imposed. "
         + c("SLOT_DPB") + " = 2, " + c("INGRESSI") + " = 2 input images in rotation, one slice per frame."],
        ["Headers", "Written by the driver from those parameters (" + c("vkGetEncodedVideoSessionParametersKHR")
         + "); if it had to change something (" + c("hasOverrides") + ") the log says so. SPS/PPS (and VPS) are put "
         "in front of every keyframe."],
        ["HEVC level fix", "RADV (Mesa 25.0.7) wrote " + c("general_level_idc = 40") + " for level 4.0 instead of "
         "120 — the H.264 alphabet. " + c("correggi_livello_hevc()") + " fixes the byte in the returned "
         "VPS/SPS, walking the RBSP with its emulation bytes, and logs it."],
        ["Rate control", "CQP by default; with the ceiling VBR (average = working point, maximum = maximum rate, "
         "buffer in milliseconds computed from the VBV bits). Vulkan has no QVBR: the requested QP becomes the regulator's <i>minimum</i> QP."],
        ["Input, zero copy", "The DMA-BUF is imported (" + c("VK_EXT_external_memory_dma_buf") + ", "
         + c("VK_EXT_image_drm_format_modifier") + "), cached for up to " + c("IMPORTAZIONI_MAX") + " = 8 buffers "
         "and discarded when the producer's generation changes."],
        ["Input, memory", "The BGRx/RGBx pixels are uploaded as RGB and the same shader converts them."],
        ["Quality change", c("vulkanvideo_qualita()") + " changes the QP (CQP) or the floor (VBR) live; it does "
         "not force a keyframe by itself."],
    ], "«TAB» — The Vulkan Video encoder") + \
    p("<b>NVIDIA and linear buffers.</b> The NVIDIA GBM refuses a LINEAR|RENDERING buffer ("
      + c("vulkanvideo_scheda_rifiuta_il_lineare()") + " asks exactly that); " + c("vulkanvideo_modificatori()")
      + " lists the non-linear modifiers the card can import and sample, and the capture offers them (see "
      + rif("PipeWire negotiation, resize and wake-up") + " and " + rif("Slabs: zero copy on labwc") + "). On "
      "the RTX 4090 the memory comparison was 12 of 12 good (PSNR 38.6–46.2 dB, 1080p and 4K) before zero copy "
      "worked, and 28 of 28 from the GPU after.") + \
    p("<b>The bench switch.</b> " + c("REMOTIX_VULKAN_CONVERSIONE=copia") + " forces the shader to write into an "
      "intermediate image that is then copied, even where it could write the encoder's input directly, to "
      "measure that branch. It is for benches only; the product's choice is the one read from the driver.")

# ── 7.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The capture delivers RGB, the encoders want YUV 4:2:0. The conversion is always <b>BT.709, from "
       "full-range RGB to limited-range YUV</b> (Y 16–235, Cb/Cr 16–240; at 10 bits 64–940 and 64–960), and the "
       "stream's VUI says so. Who converts depends on the path.", lead=True) + \
    table(["Path", "Converter", "Notes"], [
        ["VA-API, zero copy", "The GPU's video processor (VPP, " + c("VAEntrypointVideoProc") + "), "
         + c("converti_sulla_gpu()"), "Matrix imposed: source " + c("VAProcColorStandardNone") + " full range, "
         "output " + c("VAProcColorStandardBT709") + " reduced range; regions declared"],
        ["VA-API, from memory", c("colori709.c") + " in CPU into NV12/P010, then " + c("vadiretta_carica_nv12()")
         + " / " + c("vadiretta_carica_p010()"), "Uploading RGB for the VPP was measured worse"],
        ["Vulkan, both inputs", c("vulkanvideo_rgb_nv12.comp") + " on the compute queue", "Same integer "
         "arithmetic as " + c("colori709.c") + ", same bytes (bench 19)"],
    ], "«TAB» — Who converts the colours") + \
    p("<b>The arithmetic</b> (" + c("colori709.c") + " and the shader): Kr = 0.2126, Kb = 0.0722; coefficients in "
      "fixed point with 15 fractional bits so each fits an " + c("int16") + " for " + c("pmaddwd") + "; luma "
      "(5983, 20127, 2032) sums to 28142 = 219/255 · 32768, so white gives 235 and black 16; Cb (−3298, −11094, "
      "14392) and Cr (14392, −13072, −1320) each sum to 0 — the green coefficient of Cr is 13072, not the rounded "
      "13073, so that every grey is exactly 128 (verified on all 256 greys). Chroma is the sum of each horizontal "
      "pair, filtered vertically with a 1-3-3-1 tent over four rows (swscale's filter), rounded to nearest, no "
      "dithering. At 10 bits the matrix is computed at 10 bits (876 luma levels), not 8 bits shifted, which is "
      "what swscale did; P010 stores the ten bits high in sixteen.") + \
    p("<b>Why REMOTIX's own code.</b> libswscale went with ffmpeg; libyuv (0.0.1904 on Debian trixie) converts "
      "ARGB to 4:2:0 only as BT.601 limited or JPEG full range, which would have changed the product's colours "
      "with no error anywhere. About 200 lines and no extra dependency for the installer on seven distributions. "
      "x86-64 always has SSE2 (it is in the ABI), so there is no runtime dispatch; other architectures run the "
      "same arithmetic in plain C with identical bytes. GCC 14 at " + c("-O2") + " did not vectorise the plain C "
      "(13.7 ms at 3840×2160 against 13.1 for swscale, 30 Sep 2026).") + \
    warn("leaving the VPP regions NULL means “the whole surface”, and the destination surface is aligned (1920×1088 "
         "on iHD for 1080p): the VPP then <i>scaled</i> 1080 rows to 1088. The colour statistics of the two streams "
         "matched within 0.17 levels while the drag bench read 0 marks out of 903 against 870 of 870 on the other "
         "path — a slightly blurred, slightly stretched desktop with no log line. Both regions are now the "
         "canvas, and the source is the canvas size.", "The 1088-row scaling found by refutation (22 Aug 2026).") + \
    note("the Radeon's VPP loses on chroma (phase 18 bench: −1 to −6 dB of PSNR from memory, and on zero copy "
         "with both the old and the new code); with Vulkan on AMD the shader does the conversion instead.",
         "Radeon VPP.")

# ── 7.7 ─────────────────────────────────────────────────────────────────────
S7 = p("Since phase 18 REMOTIX writes H.264 and HEVC headers itself. " + c("scrittore_bit.c") + " knows no codec: "
       "it knows bits, Exp-Golomb and the " + c("00 00 03") + " rule. Which fields to write, and in which order, "
       "is in " + c("vadiretta.c") + ", with the standard's clause beside each line. It is the mirror of the "
       "reader " + c("LettoreBit") + " that " + c("codificatore.c") + " has had since 12 Aug 2026 to read back "
       "what was produced.", lead=True) + \
    table(["Function", "Writes"], [
        [c("sb_u(s, n, v)"), "The " + c("n") + " low bits of " + c("v") + ", most significant first (n ≤ 32)"],
        [c("sb_flag()"), "One bit"],
        [c("sb_ue()") + " / " + c("sb_se()"), "Unsigned / signed Exp-Golomb (H.264 9.1, H.265 9.2); signed maps k "
         "to (−1)<sup>k+1</sup>·⌈k/2⌉"],
        [c("sb_chiudi_rbsp()"), c("rbsp_trailing_bits()") + ": a 1 then zeros to the byte (also H.265 "
         + c("byte_alignment()") + ")"],
        [c("sb_allinea_con_uni()"), c("cabac_alignment_one_bit") + ": <i>ones</i> to the byte, the tail of an "
         "H.264 slice header under CABAC"],
        [c("sb_copia_bit()"), "Copies a run of bits from a source: used to rewrite the head of an SPS and copy the "
         "tail as is"],
        [c("nal_annexb()"), c("00 00 00 01") + ", the NAL header unchanged (1 byte H.264, 2 bytes HEVC), then the "
         "RBSP with emulation prevention (" + c("00 00 0x") + " with x ≤ 3 → " + c("00 00 03 0x") + "); 0 if the "
         "output is too small"],
    ], "«TAB» — The bit writer") + \
    p("A field that does not fit sets " + c("traboccato") + " (overflowed) and whoever closes the NAL sees it: a truncated "
      "header looks like a header. The NAL header itself receives no emulation bytes, as in ffmpeg's "
      + c("cbs_h2645") + ".") + \
    h4("The cropping window rewrite (D-023)") + \
    p("Measured 27 Sep 2026 on the Radeon RX 6800 (Mesa radeonsi 25.0.7): HEVC at 2544×1344 produced a stream "
      "<i>declaring</i> 2560×1344 — the card codes the multiple of its 64-pixel block and does not write the "
      "conformance window. The byte check rightly refused a stream whose size differs from the canvas, Chrome "
      "chose HEVC, Chrome's canvases are never multiples of 64: a session black forever. "
      + c("cornice_al_suo_posto()") + " (“the window in its place”) decides on the first SPS of each encoder context: if the stream is larger "
      "than the canvas by less than 64 pixels on each side and by even amounts, the window is written. "
      + c("riscrivi_sps_con_cornice()") + " re-reads the SPS up to the cropping flag, rewrites the head identical, "
      "sets the flag with the four offsets (in chroma units, i.e. half pixels for 4:2:0, added to any that "
      "existed), copies the tail bit by bit to the stop bit, and puts the NAL back with its emulation bytes. "
      "This is legal because nothing after the window depends on its position. Only keyframes carry an SPS, so "
      "only they are touched; any other mismatch remains an error. Measured: the 2560 stream cropped to 2544 "
      "decoded against the original at PSNR 50 dB.")

# ── 7.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Decision D1 of phase 2: <b>pure Annex-B and no " + c("description") + "</b>. Every keyframe carries its "
       "parameter sets in front (H.264: SPS, PPS, IDR; HEVC: VPS, SPS, PPS, IDR), so a client that attaches late "
       "decodes from the first key it sees. Chromium decides the stream form from the presence of the "
       + c("description") + ", not from the " + c("hev1") + "/" + c("hvc1") + " prefix (measured 12 Aug 2026).",
       lead=True) + \
    p("Before any byte leaves, " + c("forma_va_bene()") + " checks it, because a decoder fed the wrong shape does "
      "not complain: it paints black, or paints at the old size, three links further down.") + \
    ul(["the frame starts with a start code (not a length prefix);",
        "a keyframe has its parameter sets before the IDR;",
        "the SPS is read with the bit reader (" + c("leggi_sps_h264()") + ", " + c("leggi_sps_hevc()")
        + "), and the depth and the displayed size in the bytes must equal what was requested; the size coded "
        "and the size displayed are kept apart (" + c("larghezza_codificata") + " vs " + c("larghezza_flusso")
        + ", coded width vs stream width: on radeonsi 1080p is coded as 1088 and cropped).",
        "a frame larger than 16 MiB is never sent (" + rif("Frame ceiling and quality steps") + ")."]) + \
    p("<b>The confession.</b> " + c("codificatore_confessione()") + " returns what the encoder actually did, from "
      "two independent witnesses: the context (component opened, path, vendor, entry point verified, size limits, "
      "rate-control mask and mode read back, working point, maximum rate, VBV in bits and milliseconds) and the bytes "
      "(depth, profile, level, tier, sizes, chroma format, " + c("stringa_codec") + "). If they disagree, the "
      "component disobeyed: " + c("ha_obbedito") + " (obeyed) becomes false and nothing is sent. The reason is history: "
      "libsvtav1 printed «Error parsing option» on an unknown option and exited 0; v1 had a CBR nobody asked for "
      "that only the bandwidth bill revealed (lesson R31).") + \
    table(["Codec", "Field in the SPS", "Level 5.1 is written as"], [
        ["H.264", c("level_idc") + " = major·10 + minor", "51"],
        ["HEVC", c("general_level_idc") + " = (major·10 + minor)·3", "153"],
        ["AV1 (reserved)", c("seq_level_idx") + " = (major − 2)·4 + minor", "13"],
    ], "«TAB» — Three alphabets for one level") + \
    p("<b>The level is imposed, then verified.</b> RCP/1 says the server must not emit a level above the client's "
      + c("video.livello") + "; the browser does not enforce it (Chrome accepted L30 on a level 3.0 stream and "
      "painted, 12 Aug 2026), so the check is the server's (decision D4). On 23 Aug 2026 a 3840×2160 H.264 "
      "stream came out at level 5.2 against a declared 5.1, because nobody had told the encoder. Now "
      + c("livello_imposto()") + " translates the ceiling into the codec's alphabet, the encoder writes it, and the "
      "child logs the level read from the bytes in decimal next to the client's (" + c("livello_in_decimi()")
      + "). The declared cost: H.264 5.1 allows " + c("MaxMBPS") + " 983,040, i.e. about 30 frames/s at "
      "3840×2160, and the encoder keeps running at 60, so the stream declares a level whose rate limit it exceeds "
      "— which is exactly what the client asked for by declaring 5.1 at 4K; halving the rate would change what "
      "the user sees and is not done here. The largest canvas, 4096×2304, is the " + c("MaxFS") + " of levels "
      "5.1/5.2.") + \
    p("A change of negotiated depth, level ceiling or capture channel order (BGRx ↔ RGBx) between two clients of "
      "the same session rebuilds the encoder, because these are fixed at opening; the next frame is a key.")

# ── 7.9 ─────────────────────────────────────────────────────────────────────
S9 = p("The GOP is infinite (" + c("chiavi_ogni") + " = 0): periodic keyframes are bandwidth spent on an "
       "insurance the protocol already buys, and on a bad line keys sent by the clock are the spiral RCP/1 "
       "forbids. A keyframe is produced exactly when one is owed.", lead=True) + \
    table(["Cause", "How"], [
        ["First frame after " + c("SESSIONE"), "A new encoder has no past; its first frame is an IDR"],
        ["First frame at a new canvas", c("codificatore_ridimensiona()") + " closes and reopens the context; a delta "
         "at the new size in Chrome HEVC raised nothing and painted a broken image at the old size (12 Aug 2026)"],
        ["The client asks", c("RICHIEDI_CHIAVE") + " → the parent sends the child a video message with "
         + c("chiave = 1") + " → " + c("debito_chiave") + " (key debt) → " + c("codificatore_chiedi_chiave()")
         + " before compressing, not after"],
        ["A delta was abandoned", "RCP/1: the server must send a key as soon as it can, without waiting to be asked"],
        ["The encoder was rebuilt", "Depth, level or channel order changed; or a quality step reopened the context"],
    ], "«TAB» — When a keyframe is produced") + \
    p("A keyframe on a still desktop has nothing to encode, because the compositor sends nothing: the child wakes "
      "the stream so a frame arrives (" + rif("PipeWire negotiation, resize and wake-up") + "). With GOP infinite "
      "the request path must exist: without anyone calling " + c("codificatore_chiedi_chiave()") + ", a client that "
      "lost one delta would keep a broken screen forever. How the page decides to ask is in "
      + rif("The browser page") + ".")

# ── 7.10 ────────────────────────────────────────────────────────────────────
S10 = p("RCP/1 forbids a video frame larger than 16 MiB: it must be re-encoded at lower quality and logged, "
        "never sent. " + c("TETTO_FOTOGRAMMA") + " is 16 × 1024 × 1024 bytes.", lead=True) + \
    table(["Constant", "Value", "Meaning"], [
        [c("QP_HARDWARE"), "26", "The constant QP the product asks (" + c("figlio.c") + "); a declared "
         "convenience value, the working point belongs to phase 9"],
        [c("CRF_DI_EMERGENZA") + " / " + c("CRF_PASSO"), "24 / 9", "Emergency CRF and step. Steps when the ceiling bites: from QP 26 the "
         "ladder is 35, 44, 51"],
        [c("RICODIFICHE_MASSIME"), "3", "Encodings allowed for a <i>delta</i> (26, 35, 44); a key walks the ladder "
         "to the end, because a key may not be abandoned"],
        [c("RISALITA_MARGINE"), "2 MiB", "Climb-back margin: a frame counts as comfortably under the ceiling below one eighth of it"],
        [c("RISALITA_ATTESA") + " / " + c("RISALITA_ATTESA_MAX"), "120 / 3840 frames", "Climb-back wait: quiet frames before "
         "climbing one step; doubles on every relapse (about 2 s to 64 s at 60/s)"],
    ], "«TAB» — The ceiling and the quality ladder") + \
    p("The step was 6 until 22 Aug 2026: at 7680×4320 on nearly incompressible content QP 38 gave 16.654 MiB (8 "
      "times out of 8 over, by 4 %) while QP 44 gave 11.056 MiB; a wider step costs a fraction of one more "
      "attempt (91–108 ms each on the GPU at 8K). At the user's canvas (2560×1080) the largest of 404 real keys "
      "was 21,433 bytes, 0.13 % of the ceiling: the defect is real and far from urgent. Every quality change "
      "closes and reopens the context, and the next frame is a key.") + \
    p("Two server-wide switches change what the user sees and are therefore <b>off by default</b> (invariant I6): "
      + c("--qualita-risale") + " (" + c("codificatore_qualita_risale()") + ", climbing back up the quality ladder) and "
      + c("--tetto-banda-mbit N") + " (" + c("codificatore_tetto_banda()") + ", QVBR on VA-API / VBR on Vulkan "
      "with maximum rate = 80 % of the declared floor, working point = 75 % of the maximum rate — never equal, or the Intel driver "
      "deduces CBR — and a 40 ms VBV). Their numbers, measurements and the third witness (the bytes per 10 s "
      "window) are described in " + rif("Quality, degradation and budget") + ".")

# ── 7.11 ────────────────────────────────────────────────────────────────────
S11 = p(c("codificatore_ridimensiona()") + " reopens the encoder at the new size; the first frame after is a "
        "true key. The size it receives has already been checked by " + c("rcp_misura_ammessa()") + ": at least "
        "320×240, at most 4096×2304, even sides; a larger request is <i>reduced</i> (the side that overflows goes "
        "to the maximum, the other stays), a smaller one is refused.", lead=True) + \
    p("The 4096-pixel width is the user's decision of 1 Oct 2026 (“4096 max width is fine; it is more than 4K”): "
      "H.264 on the Intel GPU stops there (32–4096 per side), and Firefox receives only H.264. Before, the legal "
      "canvas reached 7680×4320 and wider H.264 canvases had nowhere to go. The driver's own maximum is still "
      "read at every opening (" + c("misura_massima_l") + "/" + c("misura_massima_a") + ", maximum width/height), because another card "
      "may declare less.") + \
    p("Encoding at a size that is not a multiple of the block: H.264 writes the cropping window itself (16-pixel "
      "macroblocks); HEVC relies on the driver, and where the driver does not write it, on D-023 ("
      + rif("Writing the bitstream headers") + "). With Vulkan on the Radeon the capture slabs stay at the maximum "
      "canvas across resizes (" + rif("Slabs: zero copy on labwc") + ").")

# ── 7.12 ────────────────────────────────────────────────────────────────────
S12 = p("Phase 18 (closed 30 Sep 2026) removed ffmpeg; phase 19 (closed 3 Oct 2026) removed the CPU encoders. "
        "Both were accepted only on measured equivalence.", lead=True) + \
    table(["Work", "Before", "Now", "Licence"], [
        ["GPU encoding", c("h264_vaapi") + ", " + c("hevc_vaapi") + " in libavcodec", c("vadiretta.c")
         + " on libva; " + c("vulkanvideo.c") + " on Vulkan", "MIT / Apache-2.0"],
        ["CPU fallback", "libx264, libx265, libsvtav1; then OpenH264 and SVT-AV1 (phase 18)", "None (phase 19)", "—"],
        ["Audio", "Opus through libavcodec", "libopus directly (" + rif("Audio and clipboard") + ")", "BSD"],
        ["Colour conversion", "libswscale", c("colori709.c") + ", the VPP, the shader", "REMOTIX"],
    ], "«TAB» — What ffmpeg did, and what replaced it") + \
    p("The reason was licensing: REMOTIX must have no GPL dependency, and the distributions' libavcodec is GPL. "
      "The product binary no longer links libavcodec, libavutil or libswscale (verified with " + c("ldd")
      + " and " + c("nm -D") + ": 0 " + c("av_") + "/" + c("sws_") + " symbols).") + \
    table(["Measurement (test server: i5-13500T, Intel UHD 770 iHD 25.2.3, Radeon RX 6800 radeonsi 25.0.7)",
           "Result"], [
        ["Zero copy, old vs new, 120 frames, H.264 / HEVC 8 / HEVC 10, 1080p and 4K, both cards ("
         + c("banchi/18-scheda/18-confronto.sh") + ", 30 Sep 2026)", "Identical: PSNR/SSIM equal to the sixth "
         "digit, bytes equal (±2 in H.264 = the SEI string), same profile and level, encode time equal (Intel "
         "H.264 1080p 2118 → 2113 µs; HEVC 4K 7368 → 7340 µs)"],
        ["Chrome 154 decoding the 28 H.264 streams with WebCodecs", "120/120 each, pixel fingerprints equal on zero "
         "copy, key on demand, new canvas and ceiling"],
        ["From memory, after returning to CPU conversion", "Quality equal (Intel 1080p H.264 38.926 → 38.925 dB), "
         "preparation time halved (1080p 4024 → 1964 µs; 4K 16720 → 7816 µs). The intermediate attempt with the "
         "VPP from memory was worse (−1.0 dB and +82 % bytes at 1080p H.264) and was dropped"],
        ["Functional suite on the four desktop test boxes, Firefox 140 and Chrome 154, 3840×2160",
         "673 PASS, 0 FAIL, 0 BLOCKED (30 Sep 2026)"],
        ["Whole chain, 4K, 1 user per desktop, old binary with ffmpeg vs new", "Indistinguishable: product latency "
         "p95 35.3 / 38.7 / 36.1 / 36.6 ms (GNOME / KDE / XFCE / LXQt) against 33.2 / 39.6 / 36.4 / 36.2; encode "
         "median 7.9–8.0 ms"],
        ["The same chain with OpenH264 in CPU (phase 18 only)", "4K encode 24–26 ms per frame vs 7.9 on the GPU; "
         "p95 latency 87–124 ms, DEGRADED at one user on all four desktops"],
    ], "«TAB» — The evidence that let phase 18 in") + \
    p("The last number is part of why phase 19 removed the CPU path altogether (the user, 1 Oct 2026: “no CPU "
      "without a GPU; today even VMs can have hardware acceleration”). Without a capable GPU the installer's "
      "preflight refuses the machine with the reason, and a server that starts anyway offers no codec. A VM with "
      "a passed-through or virtual GPU works; a VM without one does not.") + \
    note("on the Radeon RX 6800 (VCN 3.0, radeonsi 25.0.7) one frame in about 50 takes ~31 ms instead of 8.7: groups "
         "of exactly five slow frames every 12–40 s, p99 30.9 ms, identical with libavcodec and with libva direct "
         "(30 Sep 2026, KDE and GNOME 4K). It is inside the driver's encode call, outside REMOTIX's scope by the "
         "user's decision, and documented for the Mesa developers in " + c("fasi/16-a3-radeon-vcn.md")
         + ". Since phase 19 the Radeon encodes through Vulkan; whether the anomaly persists there is not settled "
         "yet.", "Radeon anomaly A3.")

# ── 7.13 ────────────────────────────────────────────────────────────────────
S13 = p("Every encoded frame carries its costs separately, so that a drop in frame rate can be attributed. "
        "They are logged for the first frame and summarised afterwards; performance figures with their hardware "
        "are in " + rif("Performance and capacity") + ".", lead=True) + \
    table(["Field of " + c("CodificatoreFotogramma"), "What it measures"], [
        [c("us_conversione"), "RGB → YUV: the VPP or the shader on the GPU, or " + c("colori709.c") + " in CPU"],
        [c("us_caricamento"), "Memory → GPU upload; <b>0 on zero copy</b>, where the stretch does not exist"],
        [c("us_codifica"), "From handing the input to the encoder to the bytes read back"],
        [c("ricodifiche"), "Re-encodings forced by the 16 MiB ceiling (> 0 means it bit)"],
        [c("trattenuto"), "The encoder did not deliver the frame at once (one frame of delay)"],
        [c("chiave"), "Keyframe (RCP/1 type " + c("0x0301") + ") or delta (" + c("0x0302") + ")"],
    ], "«TAB» — The timings of one frame") + \
    table(["Constant", "Value", "File"], [
        [c("NODO_RENDERING"), c("/dev/dri/renderD128"), c("figlio.c")],
        [c("POTENZA_RENDERING"), c("CODIFICATORE_POTENZA_LA_DICHIARATA"), c("figlio.c")],
        [c("QP_HARDWARE"), "26", c("figlio.c")],
        [c("CODEC_MAX"), "4 (index by codec number)", c("figlio.c")],
        [c("PROVA_LATO") + " / " + c("PROVA_GIRI"), "256 / 8 (probe side in px / probe attempts)", c("figlio.c")],
        [c("TETTO_FOTOGRAMMA"), "16 MiB", c("codificatore.c")],
        [c("ALLINEAMENTO_SCHEDA"), "64 bytes (DMA-BUF stride)", c("codificatore.c")],
        [c("IMPORTATE_MAX") + " / " + c("SUPERFICI_PRONTE"), "8 / 4 (imported buffers / ready surfaces)", c("codificatore.c")],
        [c("BANDA_FINESTRA_US"), "10 s", c("codificatore.c")],
        [c("RICOSTRUITE") + " / " + c("CODED_MARGINE"), "3 / 64 KiB", c("vadiretta.c")],
        [c("SLOT_DPB") + " / " + c("INGRESSI") + " / " + c("IMPORTAZIONI_MAX"), "2 / 2 / 8", c("vulkanvideo.c")],
    ], "«TAB» — Encoder constants") + \
    tip("the log area of the encoder is " + c("video") + "; the line that starts with " + c("aperto:") + " (opened) names the codec, "
        "depth, component, node, vendor and (on VA-API) the entry point actually in force, and the line before it says "
        "which path was taken and whether it was asked by name or by capability. "
        + c("remotix --prova-codifica") + " with " + c("--codifica vulkan") + " or " + c("--codifica vaapi")
        + " reproduces one path in isolation; the comparison benches are " + c("banchi/18-scheda/18-confronto.sh")
        + " and " + c("banchi/19-vulkan/19-confronto.sh") + ", and the shader is rebuilt with "
        + c("banchi/19-vulkan/19-shader.sh") + ".", "Diagnosis.")

CHAPTER = ("Video encoding", [
    ("Encoding at a glance", S1),
    ("Codecs and their negotiation", S2),
    ("Choosing the GPU path", S3),
    ("VA-API without libavcodec", S4),
    ("The Vulkan Video encoder", S5),
    ("BT.709 colour conversion", S6),
    ("Writing the bitstream headers", S7),
    ("Bytes, levels and the confession", S8),
    ("Keyframes on demand", S9),
    ("Frame ceiling and quality steps", S10),
    ("Resizing the encoder", S11),
    ("Removing ffmpeg and the CPU path", S12),
    ("Encoder timings and constants", S13),
])
