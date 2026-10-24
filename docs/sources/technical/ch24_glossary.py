from build import c, dl, p, rif


def v(*titoli):
    return " See " + ", ".join(rif(t) for t in titoli) + "."


# ── The project's own words ─────────────────────────────────────────────────
# Since the English rename (DECISIONS.md §10.38, §10.45) the identifiers are English; many source files still
# carry their Italian names until the file-rename step (helper.c, child.c, session.c…), so a term is given
# with the file that holds it.
NOMI = [
    ("actor", "One simulated user of the stress benches: its own process, browser, labwc and clock, no conductor ("
     + c("16-actor.py") + ")." + v("Stress and capacity benches")),
    ("attach slot", "A user's place in RCP's registry: one per user, freed on detach or after 30 s of silence. The "
     "logind and Mutter <i>seat</i> stays <i>seat</i>." + v("Detach and reattach")),
    ("backstop", "A time limit that ends a wait whatever happens (" + c("CLIPBOARD_BACKSTOP") + ")."),
    ("belts", "The three system settings that forbid power-off, reboot and suspend: a polkit rule, logind key "
     "settings and sleep settings. The packages install the polkit rule active in " + c("/usr/share/polkit-1/rules.d/")
     + " and ship the other two inert in " + c("/usr/share/remotix/belts/") + "."
     + v("The power belts")),
    ("bench, benches", "A test or a measurement, with its scene, its verdict and its results kept next to it, in "
     + c("benches/") + ". " + c("BENCH_ON") + " is the build switch of the bench functions, 0 in the product."
     + v("The bench folder")),
    ("boxes", "The podman containers with systemd and the real graphics card in which the safety net runs, one per "
     "desktop (" + c("rete11-gnome") + " … " + c("rete11-lxqt") + ")." + v("The boxes of the safety net")),
    ("bridge", c("struct bridge") + ", which carries the transport and the children table to the callbacks; "
     + c("main.c") + " is the only file that knows both." + v("The parent process")),
    ("budget", "The optional composition budget: an admission check in megapixels per second, off by default ("
     + c("--budget-mpixel-s") + ")." + v("The composition budget")),
    ("canvas", "The size of the remote desktop, agreed at attach (" + c("FIT_CANVAS") + ", " + c("CANVAS")
     + "), 320×240 to 4096×2304." + v("Canvas and view")),
    ("cap, ceiling", "A hard limit: " + c("--session-cap") + " (10 stages), " + c("FRAME_CAP")
     + " (16 MiB per frame), the handshake ceilings."
     + v("Admission: the session cap and the budget", "Handshake deadlines and session states")),
    ("capture", "Reading the pixels of the session's virtual output from the compositor: a PipeWire node on GNOME "
     "and KDE, screencopy on labwc (" + c("capture.c") + ", " + c("wlroots.c") + ")." + v("Capture at a glance")),
    ("catalogue", c("catalog.json") + ", the supported distributions, desktops, minimum versions and rules, "
     "compiled into the engine." + v("The catalogue of platforms")),
    ("certify", "In a bench, " + c("--certify") + " runs the pure judges on synthetic inputs that must give red and "
     "inputs that must stay green; in the installer, the platform certification after installing ("
     + c("certify.go") + ")." + v("Rules every bench follows", "Verification and the certificate")),
    ("chatter", c("--verbose") + ": frame-by-frame detail lines from transport, capture and encoder, never sent "
     "to the journal." + v("Diagnostic instruments")),
    ("child", "One process per admitted user, running as that user: it opens the logind session, starts the desktop "
     "and holds the stage. In " + c("ps") + " it is " + c("remotix-child --internal-child") + " (" + c("child.c")
     + ")." + v("The per-user child process")),
    ("clear (the video queue)", "The video queue threshold (" + c("--clear-threshold-ms") + "): an old delta is "
     "abandoned only if the queue cannot drain in time." + v("The video queue threshold")),
    ("climb", "One ramp of the stress campaign, adding users level by level (" + c("16-climb.py") + ")."
     + v("Stress and capacity benches")),
    ("clipboard", "Plain text only, in both directions, announced first and pulled on demand (" + c("clipboard.c")
     + " on GNOME, " + c("clipboard_kde.c") + " on KDE and labwc)." + v("Clipboard at a glance")),
    ("confession", "What the encoder declares it really produced, read back from the bytes: codec string, depth, a "
     "promotion from 8 to 10 bits, the route used (" + c("EncoderConfession") + ")." + v("Bytes, levels and the confession")),
    ("cursor, shape", "The pointer is drawn by the page; only its shape travels (" + c("CURSOR_SHAPE") + "). Where "
     "the compositor does not send it, an encoded theme of 1×1 coloured images and a dictionary recover it ("
     + c("cursor.c") + ", " + c("shape.c") + ")." + v("The cursor channel", "The encoded cursor theme")),
    ("dead line", "The detector that closes a connection which has stopped carrying anything: 5 s of stalled video "
     "output, or 10 s without a client packet. On by default; " + c("--no-dead-line") + " turns it off."
     + v("The dead line")),
    ("defect", "Something wrong in the product or in a bench, found and to be repaired. Never the same word as "
     "<i>fault</i>."),
    ("denied-users", "The list read by " + c("pam_listfile") + " in the PAM file (" + c("/etc/remotix/denied-users")
     + "); it holds " + c("root") + ". Missing, it makes PAM refuse everyone." + v("The PAM service files")),
    ("diary", "The page's " + c("/diary") + " endpoint of 1.0: the page wrote its own lines into the server log. Gone from the product and from test builds since 1.5."
     + v("The page server")),
    ("encoder", "The front of video encoding: picks Vulkan Video or VA-API by capability, checks the bytes, owes "
     "keyframes, enforces the 16 MiB ceiling (" + c("Encoder") + ", " + c("encoder.c") + ")."
     + v("Encoding at a glance")),
    ("engine", c("remotix-install") + ", the only place with installation logic; the TUI and the command line are "
     "its faces." + v("The installer at a glance")),
    ("eviction", "Ghost eviction (" + c("--eviction-ms") + ", 15 s): a slot held by a silent client goes to a new "
     "client of the same user." + v("Ghost eviction and audio silence")),
    ("fault", "A fault grafted on purpose by a bench to prove that its judge sees it. Never the same word as "
     "<i>defect</i>."),
    ("fingerprint", "Four different things: the SHA-256 of the session certificate the page fetches from "
     + c("/fingerprint") + "; the installer's machine fingerprint that binds a plan; the " + c("fingerprints")
     + " target of the Makefile (the twin check); the folder fingerprint of test R1."
     + v("serverCertificateHashes and the fingerprint", "The machine fingerprint")),
    ("finding again, found again", "Live REMOTIX desktops that no child holds, found at startup after a restart and "
     "counted until their user returns (" + c("RediscoveredDesktop") + ", " + c("rediscover.c") + ")."
     + v("Desktops found again after a restart")),
    ("graft", "Code added on purpose to a copy of the product or of a third-party example, a fault grafted by a "
     "bench included. Never <i>inject</i>, which is only for input."),
    ("helper", "The PAM helper process: a dispatcher started once at boot that forks one short-lived grandchild per "
     "password check, so that PAM, which can take seconds, never blocks the server's single loop ("
     + c("struct helper") + ", " + c("helper.c") + ")." + v("The PAM helper process")),
    ("hook", c("11-hook.sh") + ", the git " + c("pre-push") + " hook that runs the safety net chosen by the "
     "paths that changed." + v("When the net runs: the hook")),
    ("increment", "A new capability or desktop added while every certified one is kept, through the gates CP0 "
     "onwards." + v("The increment method")),
    ("key", "That is keyframe. " + c("REQUEST_KEY") + " asks for one; the child keeps a debt (" + c("key_debt")
     + ") until it has produced it." + v("Keyframes on demand")),
    ("keyboard", c("keyboard.c") + ", from a character to the key positions that produce it."
     + v("From a letter to key positions")),
    ("layout", "The keyboard layout. Proposed by the page in " + c("ATTACH") + "; the session's real keymap is "
     "always the one in force." + v("Keyboard layout negotiation")),
    ("LETTER, KEY_POSITION", "Text travels as characters, commands as evdev key positions; the child turns a letter "
     "into the keys that produce it on the session's layout." + v("Keyboard: letters and positions", "From a letter to key positions")),
    ("link, loop, ring", "Three senses, three words. <i>Link</i>: one link of the chain a phase builds — capture, "
     "encoding, wire, decoding, input; each link has its own bench. <i>Loop</i>: a delay loop or a closed loop, "
     "input to glass included. <i>Ring</i> only for the audio ring buffer."),
    ("log", "In the server, the log module (" + c("log.c") + "), the only place that writes lines. In the "
     "installer, the write-ahead log of an operation (" + c("log.go") + ")."
     + v("The log module", "The write-ahead log and resume")),
    ("mark", "The bench marker " + c("BENCH_MARK") + ", a coloured square painted after a known delay and refused "
     "in the product; and the image mark read by " + c("03-mark.py") + "." + v("The bench marker: BENCH_MARK")),
    ("meshes", "The checks of the safety net, C1 to C24." + v("The meshes C1 to C24")),
    ("nested KWin", "On KDE, KWin runs inside a labwc without a screen that the server starts in "
     + c("--kwin-nested") + " mode; at a reattach of another size REMOTIX resizes labwc's output and KWin follows. "
     "Without labwc, KWin " + c("--virtual") + " as before, declared (" + c("kwin.c") + ", DECISIONS.md §10.40)."
     + v("KDE Plasma sessions")),
    ("operation", "One installation, upgrade or uninstallation of the engine, with its folder, state, plan and "
     "write-ahead log." + v("Operation states")),
    ("plan", "The list of steps the installer will do, with how each is done, verified and undone, shown before the "
     "single question." + v("The installation plan")),
    ("postponement", "The pacer putting a send off to a later moment. <i>Resend</i> is only QUIC retransmission."),
    ("presence", "The table of " + c("main.c") + " that runs each user's abandonment clock, from the birth of the "
     "stage to its end." + v("Where state lives")),
    ("rate", "The frame rate. The rate regulator holds a frame back when two live deltas are still queued (the "
     + c("backlog") + "); the only mechanism that lowers the frame rate; on by default, " + c("--no-adaptive-rate")
     + " turns it off." + v("The rate regulator")),
    ("reserve", c("--reserve") + ": the share of an idle tenant's worst case the budget keeps aside."
     + v("Admission: the session cap and the budget")),
    ("round", "One full pass of a suite or a net (round 1, round 2); never <i>run</i>."),
    ("routes", "The hardware encoding paths, " + c("vulkan") + " and " + c("vaapi") + " (" + c("--encoding-route")
     + "); the installer requires at least one with a capable card." + v("Encoding routes and the card verdict")),
    ("seam", "A header that joins two pieces and is owned by the coordinator, not by either piece: " + c("input.h")
     + ", " + c("clipboard.h") + ", " + c("cursor.h") + ", " + c("keyboard.h") + ". The defects of phase 3 lived "
     "between pieces each correct on its own."),
    ("sentinel", "The code that asks logind whether a user has a local graphical session, and checks that the remote "
     "one has no seat (" + c("sentinel.c") + ")." + v("The logind sentinel")),
    ("session", "Two meanings: the RCP session of one connection, and the user's graphical session, started headless "
     "by the child (" + c("session.c") + ")." + v("Birth of a session")),
    ("single package", "The " + c("remotix-X.Y.Z-R.run") + " file: a shell header and a tar.gz with the engine and "
     "the REMOTIX packages of every target." + v("The .run file format")),
    ("slab", "On labwc, a GBM buffer REMOTIX owns on the compositor's render node, into which the compositor copies "
     "each frame (" + c("WlrSlab") + ")." + v("Slabs: zero copy on labwc")),
    ("sound", "The session's virtual sink and the capture of its monitor (" + c("sound.c") + ")."
     + v("The session sink and its capture")),
    ("stage", "What the child mounts on the user's desktop: virtual monitor, capture, input, clipboard, cursor. It "
     "belongs to the session and outlives every client (invariant I4); the cap counts stages ("
     + c("stage_count()") + ")." + v("The stage and the virtual monitor")),
    ("suite", "The functional suite: what a user does, on four desktops with real Firefox and Chrome."
     + v("The functional suite")),
    ("tenant", "A user being served. Tenants created by benches are named " + c("c&lt;n&gt;u&lt;n&gt;")
     + " so that cleanup never touches a person's account." + v("Rules every bench follows")),
    ("terrain", "What a bench needs before it can judge (users, boxes, server, scene); exit code 2 means the terrain "
     "does not hold." + v("Rules every bench follows")),
    ("twin", "The copy of " + c("rcp.c") + ", " + c("rcp.h") + " and " + c("authentication.c") + " in "
     + c("benches/rcp/") + "; " + c("make") + " refuses to build if the two differ (" + c("TWIN")
     + " names the folder)." + v("The twin-copy check")),
    ("UNBLOCK", "The request on the unblock socket (" + c("--command-socket") + ") that lifts every ban level (user, key, /48) of an address and its recidivism."
     + v("The unlock command socket")),
    ("verdict", "PAM's yes or no, handed back to the server; never sent sooner than one second after "
     + c("CREDENTIALS") + "." + v("Credentials, the fixed delay and the address ban")),
    ("view", "The size at which the page draws the canvas; it follows the window and never touches the desktop ("
     + c("VIEW") + ")." + v("Canvas and view")),
    ("witness", "An independent observer a bench uses to see an effect from outside the piece being judged — never "
     "the sender's own log."),
    ("yardstick", "The measure a result is compared against; never <i>meter</i>."),
    ("zero copy", c("ZERO_COPY") + ": the frame never leaves the GPU between compositor and encoder; the default."
     + v("Zero copy and the memory fallback")),
    ("FAREWELL", "The RCP message that closes a session, always with a reason code; the reason is repeated in the "
     "WebTransport close code." + v("RCP: the farewell", "Disconnect reasons")),
]

# ── Names that left the product ─────────────────────────────────────────────
RETIRED = [
    ("Retired options", c("--ritmo-adattivo") + ", " + c("--linea-morta") + ", " + c("--linea-morta-permille")
     + " and " + c("--sblocca") + " were removed, not renamed: the rate regulator and the dead line are on by "
     "default (" + c("--no-adaptive-rate") + ", " + c("--no-dead-line") + " turn them off). The alias " + c("--ban")
     + " is gone: the option is " + c("--ban-file") + ". The server refuses an unknown option."),
    ("Italian public names", "Options, environment variables, data keys, RCP and wire names, log areas and page "
     "names were renamed to English by hand-curated tables, with <b>no aliases and no upgrade migration</b>: "
     "REMOTIX had never been released (DECISIONS.md §10.38, §10.45). The committed append-only registers of the "
     "benches keep their file names, and their readers accept both spellings of the keys."),
    ("Retired benches", "Benches that can no longer run left the repository on 11 Oct 2026 (" + c("07-b64-*")
     + ", " + c("07-b65") + ", " + c("09-b70") + ", " + c("09-b76") + ", " + c("09-b77") + ", " + c("09-b79")
     + ", " + c("09-b81") + ", " + c("09-b84") + " and others); their measurements stay in the phase documents "
     "(DECISIONS.md §10.44)."),
    ("AV1", "A video codec offered until phase 18; its RCP number 2 is reserved forever and never reused."
     + v("Codecs and their negotiation")),
]

# ── Protocol and technology terms ───────────────────────────────────────────
A_L = [
    ("Annex B", "The H.264/HEVC stream form with a start code before every NAL unit. REMOTIX sends pure Annex B, "
     "with parameter sets before every keyframe and no " + c("description") + "." + v("Bytes, levels and the confession")),
    ("Attach", "Asking for a desktop after admission: " + c("ATTACH") + " carries the wanted canvas, the view and the "
     "layout; " + c("SESSION") + " answers new or resumed." + v("ATTACH and SESSION: attaching to a desktop")),
    ("BT.709", "The colour matrix of every REMOTIX stream: full-range RGB to limited-range YUV 4:2:0."
     + v("BT.709 colour conversion")),
    ("Bubble Tea", "The Go terminal interface library the installer's TUI is built on, with lipgloss."
     + v("The installer TUI")),
    ("CDP", "Chrome DevTools Protocol: how the benches drive real Chrome, without a WebDriver server."
     + v("Driving real browsers")),
    ("Capability", "A name-value pair exchanged in " + c("HELLO") + " and " + c("HERE_I_AM") + "; within RCP/1 the "
     "protocol grows only through capabilities." + v("HELLO and HERE_I_AM: capability negotiation")),
    ("D-Bus", "The system and session message buses. The installer talks to systemd, logind and firewalld over the "
     "system bus; the child talks to Mutter and KWin over the user's session bus, which root cannot join."
     + v("The per-user child process")),
    ("Datagram", "An unreliable QUIC message. Only audio uses datagrams, one block each."
     + v("Streams versus datagrams", "Audio datagrams")),
    ("Decision numbers", "References such as DECISIONI §10.36, D1–D14 (installer decisions) or D-006 (page "
     "decisions) point to the decision register." + v("The decision register")),
    ("Delta frame", "A frame predicted from the previous ones (" + c("V_DELTA") + "); losing one ruins the following "
     "ones until a keyframe." + v("Key frames and abandonment")),
    ("DeX", "Samsung's desktop mode for Android phones, with mouse and keyboard: the main Android use of REMOTIX."
     + v("Browsers supported and untested")),
    ("DMA-BUF", "A Linux buffer shared between devices and processes by file descriptor; how frames stay on the GPU "
     "from compositor to encoder." + v("Zero copy and the memory fallback")),
    ("Drop-in", "A systemd override file. REMOTIX writes user-unit drop-ins that make gnome-shell headless and "
     "start KWin nested at the canvas size." + v("GNOME sessions", "KDE Plasma sessions")),
    ("EIS, libei", "Emulated input: the library and protocol through which a sender injects input into a compositor. "
     "Used on GNOME and KDE; labwc has none." + v("Injection through libei")),
    ("Evidence marks", c("[M]") + " measured, " + c("[R]") + " read in reference code, " + c("[S]") + " read in a "
     "specification, " + c("[?]") + " assumed." + v("Evidence marks")),
    ("Exp-Golomb", "The variable-length integer coding of H.264/HEVC headers, written by " + c("bit_writer.c")
     + "." + v("Writing the bitstream headers")),
    ("Extended CONNECT", "The HTTP/3 request (RFC 9220) that opens a WebTransport session, here on " + c("/rcp/1")
     + "." + v("The WebTransport layer")),
    ("GBM", "Generic Buffer Management: the Mesa API used to allocate the slabs on labwc."
     + v("Slabs: zero copy on labwc")),
    ("GOP", "Group of pictures. REMOTIX uses an infinite GOP: keyframes only when one is owed."
     + v("Keyframes on demand")),
    ("H.264, HEVC", "The two video codecs REMOTIX encodes, numbered 3 and 1 in RCP. Firefox on Linux receives "
     "H.264 only." + v("Codecs and their negotiation")),
    ("Headless", "Without a physical monitor or seat: every REMOTIX session is born headless, with one virtual "
     "monitor." + v("Birth of a session")),
    ("HTTP/3", "HTTP over QUIC, provided by nghttp3; WebTransport runs on top of it." + v("The transport stack at a glance")),
    ("Invariants I1–I8", "The eight rules of " + c("CODER.md") + " §2, quoted throughout the code (I1 the rate falls "
     "only on measure, I3 the guard starts from denied, I4 the stage outlives the client…)."
     + v("Architectural principles", "Writer and reviewer")),
    ("Keyframe", "A frame decodable on its own (IDR, " + c("V_KEY") + "), carrying its parameter sets; about ten "
     "times a delta." + v("Keyframes on demand", "Keyframe request pacing")),
    ("KWin", "The KDE Plasma compositor. REMOTIX starts it nested in a screenless labwc (" + c("--kwin-nested")
     + ", " + c("--virtual") + " only where labwc is missing) and captures through "
     + c("zkde_screencast_unstable_v1") + "." + v("KDE: the KWin screencast protocol")),
    ("labwc", "The wlroots compositor under which REMOTIX runs XFCE and LXQt, and the screenless host of the "
     "nested KWin on KDE. On Alma/RHEL 10, which has none, the package ships its own labwc 0.8.4 at "
     + c("/usr/lib/remotix/labwc") + " (DECISIONS.md §10.43)." + v("XFCE sessions on labwc")),
    ("logind", "systemd's login manager: sessions, seats, local-session checks, and the termination of REMOTIX "
     "sessions at uninstall." + v("The logind sentinel")),
]

M_Z = [
    ("Marionette", "Firefox's own remote-control protocol, used by the benches to drive real Firefox."
     + v("Driving real browsers")),
    ("Mesa, RADV", "The open graphics drivers; RADV is AMD's Vulkan driver, which encodes through Vulkan Video."
     + v("The Vulkan Video encoder")),
    ("MSE", "Media Source Extensions: an optional drawing path of the page, off because it adds hundreds of "
     "milliseconds." + v("The optional paths: video worker and MSE")),
    ("Mutter", "The GNOME compositor. REMOTIX uses its direct RemoteDesktop and ScreenCast D-Bus interfaces, not "
     "the portal." + v("GNOME: the Mutter D-Bus sequence")),
    ("netem", "The Linux queueing discipline that simulates bad networks; benches take a lock before using it."
     + v("Rules every bench follows")),
    ("ngtcp2, nghttp3", "The QUIC and HTTP/3 libraries, linked statically at pinned versions."
     + v("Why ngtcp2 and nghttp3", "Static ngtcp2 and nghttp3")),
    ("NV12, P010", "The 4:2:0 YUV layouts handed to the encoder, 8 and 10 bits." + v("BT.709 colour conversion")),
    ("Opus", "The audio codec: 48 kHz stereo, 20 ms blocks, 96 kbit/s; decoded in the page by libopus compiled to "
     "WebAssembly." + v("The Opus encoder", "Playing audio in the page")),
    ("PAM", "Pluggable Authentication Modules: the machine's own password check, service " + c("remotix") + ", a "
     "copy of the distribution's sshd stack." + v("Authentication with PAM", "The PAM service files")),
    ("Phase", "A unit of the project's work with its bench and closing criterion, numbered 0 to 21 (phase 21, "
     "the licence, was closed without being built); bench file prefixes carry the phase number." + v("The documents of the project")),
    ("PipeWire", "The media server that carries the screen stream on GNOME and KDE and the session's sound."
     + v("PipeWire negotiation, resize and wake-up")),
    ("polkit", "The authorisation service; the first belt is a polkit rule that refuses power-off and its relatives."
     + v("The power belts")),
    ("QP", "Quantisation parameter. REMOTIX encodes at constant QP 26; the 16 MiB ceiling walks it to 35, 44, 51."
     + v("Encoder rate control", "The 16 MiB frame cap and the quality ladder")),
    ("QUIC", "The UDP transport (version 1, TLS 1.3 built in) under HTTP/3; one connection per client."
     + v("QUIC transport parameters")),
    ("RCP/1", "Remotix Control Protocol, version 1: what page and server say inside the WebTransport session — "
     "handshake, video, audio, input, clipboard, canvas, farewell." + v("RCP: the protocol model")),
    ("RESET_STREAM", "Abandoning a QUIC stream; how a video frame no longer useful is dropped."
     + v("Streams versus datagrams")),
    ("Rigor rule", "Whatever an RCP receiver does not understand closes the session with "
     + c("PROTOCOL_ERROR") + "; nothing is ignored." + v("RCP: the rigor rule")),
    ("RX- codes", "The installer's stable message codes, " + c("RX-&lt;AREA&gt;-&lt;NNN&gt;") + ", never reused."
     + v("The RX- code catalogue")),
    ("SBOM", "Software bill of materials, produced per package by the release." + v("Reproducible builds, SBOM and licences")),
    ("screencopy", c("zwlr_screencopy_manager_v1") + ": the wlroots protocol with which REMOTIX pulls each frame "
     "on labwc." + v("XFCE and LXQt: wlroots screencopy")),
    ("SELinux", "On Fedora and Alma a policy module gives the server its domain and lets the child pass to the "
     "user's context." + v("The service unit and SELinux")),
    ("serverCertificateHashes", "The WebTransport option by which the browser accepts a certificate by its SHA-256, "
     "only if valid for less than 14 days; hence the 13-day session certificate."
     + v("serverCertificateHashes and the fingerprint", "TLS and the two certificates")),
    ("SPS, PPS, VPS", "The parameter sets in front of every keyframe, written by REMOTIX since phase 18."
     + v("Writing the bitstream headers")),
    ("TUI", "The installer's text interface, " + c("remotix-install tui") + "." + v("The installer TUI")),
    ("uaccess", "The logind ACL that gives the seat owner the GPU; remote sessions have no seat, hence the card "
     "groups." + v("The graphics card groups")),
    ("VA-API, libva", "The video acceleration API used directly, without libavcodec, on Intel and AMD."
     + v("VA-API without libavcodec")),
    ("Vulkan Video", "The Vulkan encode extensions; the first route where the card supports it (AMD with RADV, "
     "NVIDIA proprietary)." + v("The Vulkan Video encoder")),
    ("Wayland", "The display protocol of all four desktops REMOTIX serves; X11 is not served." + v("Desktops at a glance")),
    ("WebAssembly", "The page runs libopus compiled to WebAssembly instead of the browser's AudioDecoder."
     + v("The Opus decoder build")),
    ("WebCodecs", "The browser API that decodes the video (" + c("VideoDecoder") + "); with WebTransport, the "
     "technical minimum of a client." + v("Decoding with WebCodecs")),
    ("WebGL2", "The default drawing path of the page." + v("Drawing paths: WebGL2, bitmaprenderer, 2D canvas")),
    ("WebTransport", "Streams and datagrams over HTTP/3 for web pages; server side, REMOTIX implements it itself in "
     + c("webtransport.c") + "." + v("The WebTransport layer")),
    ("wlroots", "The compositor library labwc is built on; it has no PipeWire node and no libei."
     + v("XFCE and LXQt: wlroots screencopy", "Virtual keyboard and pointer on labwc")),
    ("XKB, xkbcommon", "Keyboard layouts and keymaps; " + c("keyboard.c") + " reads the session's keymap with "
     "xkbcommon." + v("From a letter to key positions")),
    ("xrdp", "The X11 remote desktop server REMOTIX is compared against in the phase 20 campaign."
     + v("The boxes of the safety net", "Stress and capacity benches")),
]

CHAPTER = ("Glossary", [
    ("The project's own words", p("Words REMOTIX uses as terms, in the code and in this manual, with what they "
                                   "mean and the section that explains them. Since the English rename "
                                   "(DECISIONS.md §10.38, §10.45) the identifiers are English; many source files "
                                   "keep their Italian names until the file-rename step, so a term is given with "
                                   "the file that holds it.", lead=True) + dl(NOMI, "gloss")),
    ("Names that left the product", p("Names a maintainer may still meet in history, old measurements or commit "
                                      "messages, and what became of them.", lead=True) + dl(RETIRED, "gloss")),
    ("Technical terms A–L", p("Protocol and technology terms used in the manual, with what they mean for "
                              "REMOTIX.", lead=True) + dl(A_L, "gloss")),
    ("Technical terms M–Z", dl(M_Z, "gloss")),
])
