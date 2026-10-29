from build import VERSION, arrow, box, path, c, conta, dl, fig, note, numeri, p, righe, rif, table, text, tree, warn, zone

OVERVIEW = fig(
    zone(20, 12, 250, 250, "Any device (a browser)")
    + box(40, 46, 210, 54, "The page", "src/page.html, served by the server", "navy")
    + box(40, 116, 210, 54, "WebCodecs + canvas", "decodes and draws the video", "blue")
    + box(40, 186, 210, 54, "WebTransport", "RCP/1 on HTTP/3", "dark")
    + zone(330, 12, 550, 250, "The Linux machine")
    + box(350, 46, 230, 54, "Server (root)", "remotix: ports, TLS, RCP, PAM", "navy")
    + box(350, 116, 230, 54, "PAM helper", "one process per PAM check", "dark")
    + box(350, 186, 230, 54, "logind", "sessions, seats, power", "grey")
    + box(630, 46, 230, 54, "Child of user A", "runs as A: capture, encoding", "blue")
    + box(630, 116, 230, 54, "Child of user B", "runs as B", "blue")
    + box(630, 186, 230, 54, "Desktops of A and B", "GNOME, KDE, XFCE or LXQt", "light")
    + arrow(252, 73, 348, 73, "#0050C0", False, "TCP 7447: the page", 300, 64)
    + arrow(252, 213, 348, 100, "#003a90", False, "UDP 7447: QUIC", 300, 190)
    + arrow(465, 102, 465, 114) + arrow(582, 73, 628, 73) + arrow(582, 90, 628, 133)
    + arrow(745, 172, 745, 184, "#475569") + path([(862, 73), (874, 73), (874, 213), (862, 213)], "#475569")
    + text(605, 255, "one child per admitted user", 11, "#334155"),
    900, 270, "«FIG» — REMOTIX: a page in the browser, a server and one child process per user on the Linux machine")

S1 = p("<b>REMOTIX</b> is a remote desktop for Linux. A server runs on the Linux machine and serves a web page; "
       "the page and the server talk a protocol of our own, <b>RCP/1</b> (Remotix Control Protocol), over "
       "WebTransport, that is HTTP/3 on QUIC. There is nothing to install on the device the user connects from: a "
       "browser with WebTransport and WebCodecs is the client. " + c("SPECS.md") + " says what the product "
       "promises, " + c("RCP.md") + " defines the protocol, " + c("DECISIONS.md") + " records why; this manual "
       "explains how the code does it.", lead=True) + OVERVIEW + \
    p("Every user who logs in gets <b>their own graphical session</b> on the machine — GNOME, KDE Plasma, XFCE or "
      "LXQt, whichever desktop the machine has — started headless by REMOTIX, with one virtual monitor as large as "
      "the browser window. The session belongs to the user, not to the connection: closing the tab, losing the "
      "network or switching device leaves it running, and the next login finds the same windows. Only the user ends "
      "it, with “Log Out…” from the desktop menu (the page keeps no key combination of its own since 17 Aug 2026), "
      "or the server closes it after 60 minutes without input; after 30 minutes without input the server only "
      "detaches the page, and the next login finds the desktop.") + \
    p("Several users can work on the same machine at once, each in their own desktop (10 by default, set with "
      + c("--session-cap") + ", the session cap). The video is encoded only on the graphics card (VA-API on Intel and AMD, Vulkan "
      "Video on AMD and NVIDIA) in H.264 or HEVC; the audio travels as Opus in QUIC datagrams; keyboard, pointer, "
      "touch and the text clipboard travel in both directions.") + \
    table(["Item", "Value"], [
        ["Version", c(VERSION) + ", the first installable release: the number given to " + c("packaging/release.sh")
         + ", the same for every package and for " + c("remotix-install")],
        ["Server", "C (" + c("-std=gnu11") + "), Linux only, systemd, runs as root as " + c("remotix.service")],
        ["Client", "The page " + c("src/page.html") + " (HTML and JavaScript in one file), served by the server "
         "itself; a small Opus decoder in WebAssembly (" + c("src/opus-wasm/") + ")"],
        ["Installer", c("remotix-install") + ", in Go 1.25 (" + c("installer/") + ")"],
        ["Protocol", "RCP/1 over WebTransport, path " + c("/rcp/1") + "; port " + c("7447") + " on TCP (the page) "
         "and on UDP (QUIC)"],
        ["Video", "H.264 and HEVC, negotiated with the browser, encoded only on the GPU (no CPU encoder since 1 Oct "
         "2026, DECISIONS.md §10.27); no ffmpeg"],
        ["Desktops", "GNOME, KDE Plasma, XFCE and LXQt (the last two on the labwc compositor; on KDE, KWin runs "
         "nested inside a labwc without a screen, DECISIONS.md §10.40); one desktop per machine (DECISIONS.md §0.6)"],
        ["Sessions", "Wayland only; X11 applications run through XWayland"],
        ["Without input", "30 minutes: the page is detached, the desktop keeps running (" + c("--inactivity-s")
         + "); 60 minutes: the desktop is closed (" + c("--abandon-s") + "); SPECS.md §5.3"],
        ["Size", f"{righe(conta('.c') + conta('.h'))} lines of C, {righe(conta('page.html'))} lines of page, "
         f"{righe(conta('.go'))} lines of Go"],
        ["Licence", "Our own text, " + c("LICENSE.md") + " (DECISIONS.md §10.39): free for personal and "
         "non-profit use, source readable, no modifications, no redistribution; not open source. Where KWin is 6.5 or later "
         "(Ubuntu 26.04, Fedora 44, RHEL / Alma 10, Tumbleweed, Arch) the package also carries labwc 0.9.3, with a patched wlroots 0.19.2, "
         "as a separate program under its own licence, GPL-2.0 (" + c("THIRD-PARTY-LICENSES")
         + ", DECISIONS.md §10.43)"],
    ], "«TAB» — REMOTIX at a glance") + \
    p("<b>Why a protocol of our own, and why a browser.</b> REMOTIX v1 spoke RDP and stopped at its phase 11, after "
      "serving GNOME and KDE: the three walls it hit — the H.264 ceiling, an Android client decoding in software and "
      "the full colour that RDP could not carry — were walls of RDP, not of the problem (DECISIONS.md §1.1). Dropping "
      "Windows as a server removed RDP. On 9 August 2026 the dedicated clients went too (DECISIONS.md §1.6): "
      "WebTransport gives a browser exactly the bricks RCP had been designed on — independent QUIC streams, so that "
      "a frame can be abandoned without blocking the next one, and datagrams for the audio — and the protocol did "
      "not change by one line. The heritage of v1 (about 17,500 lines of C, its test benches and its studies of the "
      "desktops) is kept in " + c("fondamenta/") + " and parts of it live on in the server.") + \
    p("<b>What the user does.</b> He opens " + c("https://<machine>:7447") + ", accepts the browser's certificate "
      "warning the first time on that device (the server makes its own certificate; whoever has a domain name can "
      "install a real one), and types their Linux user name and password. The page shows their desktop, as large as the "
      "window.") + \
    table(["Browser", "Where", "Video codec", "Status"], [
        ["Chrome, Edge and the other Blink browsers", "Linux, Windows", "HEVC if the device decodes it, otherwise "
         "H.264", "supported"],
        ["Chrome", "Android", "HEVC or H.264", "supported (DECISIONS.md §7.19)"],
        ["Firefox", "Linux", "H.264 (Firefox on Linux does not decode HEVC)", "supported"],
        ["Firefox", "Windows", "—", "never tested: neither supported nor excluded"],
        ["Firefox", "Android", "—", "not supported: it has no WebCodecs (DECISIONS.md §7.18)"],
        ["Safari", "macOS, iOS", "—", "never tested"],
    ], "«TAB» — The browsers, as SPECS.md §11.5 declares them") + \
    p("<b>What REMOTIX deliberately does not do</b> (SPECS.md §12): Windows as a server; any application to "
      "install on the client; X11 desktop sessions; redirection of disks, printers, serial ports or smart cards; "
      "file transfer; images and files in the clipboard (text only); multi-monitor as a feature; stylus pressure "
      "and tilt; native multi-finger touch (a place is reserved in the protocol); recording the session to a file; "
      "compatibility with RDP, VNC or SPICE clients.") + \
    note("SPECS.md §3 sets a minimum of 480p, 25 fps, 24 bit, a desired 4K, 60 fps, 10 bit per channel, and a "
         "delay of at most 50 ms (target 40 ms) from the input arriving to the frame leaving. Since 30 September "
         "2026 these are <b>design goals, not measured promises</b> (user decision): performance tests depend too "
         "much on the hardware. The parameters the product really uses — session cap, clocks, ban, minimum "
         "bandwidth — are configuration and hold as written.", "Goals, not promises.")

S2 = p("A few concepts recur in every chapter. The manual writes their names in the code inside code spans, so "
       "that they can be searched for. Identifiers, options, environment variables and the names on the wire are "
       "in English (" + c("DECISIONS.md") + " §10.38, §10.45); most source files and folders still have their "
       "Italian names (" + c("child.c") + ", " + c("sentinel.c") + ", " + c("benches/") + "), which are renamed in a "
       "later step.", lead=True) + \
    table(["Concept", "What it is", "In the code", "More"], [
        ["<b>Server</b> (the parent)", "The process started by systemd, as root, one per machine: it listens on the "
         "two ports, speaks TLS, QUIC and RCP, and owns every connection. It never touches GLib, PipeWire or D-Bus "
         "of a user", c("main.c"), rif("The parent process")],
        ["<b>PAM helper</b>", "A dispatcher process started at boot, which forks one short-lived process per "
         "password check, so that PAM never blocks the server's loop", c("helper.c") + ", "
         + c("authentication.c"), rif("The PAM helper process")],
        ["<b>Child</b>", "One process per admitted user, running as that user: it opens the "
         "user's logind session, starts the desktop and holds capture, encoding, input, audio and clipboard. In "
         + c("ps") + " it appears as " + c("remotix-child --internal-child"), c("child.c"),
         rif("The per-user child process")],
        ["<b>Stage</b>", "What the child mounts on the user's desktop: the virtual monitor, the "
         "capture stream, the input channel, the clipboard and the cursor. It belongs to the session, not to the "
         "connection (invariant I4)", c("take_stage()"), rif("The stage and the virtual monitor")],
        ["<b>Graphical session</b>", "The user's desktop, started by the child with " + c("setsid --fork")
         + " inside the user's logind session and therefore outside the service's unit", c("session.c"),
         rif("Birth of a session")],
        ["<b>Canvas</b>", "The size of the remote desktop: the browser window's size at attach "
         "time, at most 4096×2304; it does not change while the client stays", c("ATTACH") + ", " + c("CANVAS"),
         rif("The RCP/1 protocol")],
        ["<b>View</b>", "The size at which the page draws the canvas; it follows the window "
         "without touching the desktop", c("VIEW"), rif("The browser page")],
        ["<b>Tenant</b>", "A user being served. The cap (" + c("--session-cap")
         + ", 10) counts stages, not connections", c("rcp_cap()"), rif("Where state lives")],
        ["<b>Attach slot</b>", "The place of a user's connection in RCP's registry: one per "
         "user; freed when the client detaches or falls silent for 30 s", c("struct slot") + " in " + c("rcp.c"), rif("Detach and reattach")],
        ["<b>Farewell</b> (" + c("FAREWELL") + ")", "The message that closes an RCP session, always with a reason "
         "code and a sentence: the server never closes without saying why (DECISIONS.md §4.1-bis)", c("rcp.h"),
         rif("The RCP/1 protocol")],
        ["<b>Sentinel</b> (" + c("sentinella") + ")", "The code that asks logind whether a user has a local "
         "graphical session, and checks that the remote one has no seat and cannot power the machine off",
         c("sentinel.c"), rif("The logind sentinel")],
        ["<b>Found-again desktops</b>", "Desktops left alive by a previous server process (after a restart or an "
         "upgrade), found at startup and counted until their user comes back", c("rediscover.c"),
         rif("Desktops found again after a restart")],
        ["<b>Budget</b>", "An optional admission check in megapixels per second of composition; off by default",
         c("budget.c"), rif("Quality, degradation and budget")],
        ["<b>Belts</b>", "The three system settings that forbid power-off, reboot and "
         "suspend to every user: a polkit rule, logind settings for the power key and lid, and sleep settings. "
         "The packages install the polkit rule active (§10.50) and ship the other two disabled", c("remotix-no-poweroff.rules"),
         rif("Files on the machine")],
    ], "«TAB» — Basic concepts") + \
    p("The design is held together by eight <b>invariants</b>, numbered in " + c("CODER.md") + " §2 and quoted "
      "throughout the code comments as I1…I8; they are listed in " + rif("Architectural principles") + ".") + \
    note("REMOTIX recognises the desktop from what is installed (" + c("recognize_desktop()") + " looks for "
         + c("gnome-session") + ", " + c("startplasma-wayland") + ", " + c("xfce4-session") + " and "
         + c("lxqt-session") + " in the " + c("PATH") + "). Machines with more than one desktop are out of scope "
         "(DECISIONS.md §0.6): if two are present, one is chosen — GNOME before KDE, XFCE before LXQt — and the "
         "ambiguity is written in the log at startup.", "One desktop per machine.")

S3 = p("The server's code is split by job. This is the map the manual follows chapter by chapter; the line counts "
       "of every file are in the file map appendix.", lead=True) + dl([
    (c("main.c") + ", " + c("child.c") + ", " + c("helper.c") + ", " + c("sentinel.c") + ", "
     + c("rediscover.c") + ", " + c("command.c"),
     "The processes, the main loop, the birth and death of children, the unblock socket ("
     + rif("Overall architecture") + ", " + rif("Startup and life cycle") + ")."),
    (c("transport.c") + ", " + c("webtransport.c") + ", " + c("tls.c") + ", " + c("certificates.c") + ", "
     + c("page.c"),
     "UDP and QUIC with ngtcp2 and nghttp3, the WebTransport sessions, the two certificates, the page served over "
     "TCP (" + rif("Transport: QUIC, HTTP/3, WebTransport") + ")."),
    (c("rcp.c") + ", " + c("rcp.h") + ", " + c("authentication.c"),
     "The RCP/1 state machine: handshake, credentials, ban, attach, channels, farewell ("
     + rif("The RCP/1 protocol") + ")."),
    (c("mutter.c") + ", " + c("kwin.c") + ", " + c("wlroots.c") + ", " + c("capture.c") + ", " + c("cursor.c")
     + ", " + c("shape.c"),
     "The virtual monitor and the capture on Mutter, KWin and labwc, the labwc without a screen that hosts KWin, "
     "PipeWire, dmabuf, the cursor ("
     + rif("Screen capture per compositor") + ")."),
    (c("encoder.c") + ", " + c("vadirect.c") + ", " + c("vulkanvideo.c") + ", " + c("colors709.c") + ", "
     + c("bit_writer.c"),
     "VA-API and Vulkan Video encoding, BT.709 conversion, the bitstream headers written by hand ("
     + rif("Video encoding") + ")."),
    (c("budget.c") + " and the pacing code in " + c("webtransport.c"),
     "Rate control, behaviour on bad networks, the multi-tenant budget (" + rif("Quality, degradation and budget")
     + ")."),
    (c("page.html"), "The whole client: login, WebTransport, WebCodecs decoding, drawing, input, audio, "
     "clipboard (" + rif("The browser page") + ")."),
    (c("input.c") + ", " + c("wlr_input.c") + ", " + c("keyboard.c"),
     "Keyboard, layouts, pointer, wheel and touch injected through libei or the wlroots virtual devices ("
     + rif("Input") + ")."),
    (c("audio.c") + ", " + c("sound.c") + ", " + c("clipboard.c") + ", " + c("clipboard_kde.c"),
     "The PipeWire sink, Opus, and the clipboard on each desktop (" + rif("Audio and clipboard") + ")."),
    (c("session.c"), "How each of the four desktops is born, configured, inhibited and ended ("
     + rif("The four desktops") + ")."),
    (c("log.c"), "The log, on standard error and in the systemd journal (" + rif("Logging and diagnostics")
     + ")."),
    (c("remotix.pam") + " and its variants, " + c("remotix-no-poweroff.rules") + ", "
     + c("remotix-power-keys.conf"),
     "PAM stacks per distribution family and the belts (" + rif("Security model") + ")."),
    (c("installer/"), "The " + c("remotix-install") + " engine, its catalogue and its TUI ("
     + rif("The installer") + ")."),
    (c("benches/"), "The test benches: the safety net, the functional suite, stress, the distribution boxes ("
     + rif("Testing") + ")."),
    (c("src/Makefile") + ", " + c("src/build-targets/") + ", " + c("packaging/"),
     "Building in containers, the deb, rpm and Arch packages, the release (" + rif("Build and release") + ")."),
])

S4 = p("The " + c("nic-fio/REMOTIX") + " repository on GitHub (private) holds everything: the product, the "
       "installer, the packages, the test benches, the measurements and the documents. Since " + c("DECISIONS.md")
       + " §10.38 (10 Oct 2026) everything is in English — documents, comments, the manual and what the user and "
       "the administrator read: the page, "
       "including the reasons of a farewell (" + c("REASON_TEXT") + " in " + c("page.html") + ") and the ban notice, "
       "and the server's log lines.", lead=True) + tree([
    "REMOTIX/",
    "├── src/  # the product: the server in C, the page, PAM files, build scripts",
    "│   ├── protocols/   # the Wayland protocol XML files the server is built against",
    "│   ├── build-targets/ # one container recipe per distribution, and the static QUIC libraries",
    "│   └── opus-wasm/  # the page's Opus decoder in WebAssembly, with its check",
    "├── installer/     # remotix-install, in Go",
    "│   ├── cmd/remotix-install/  # main",
    "│   ├── engine/  # the engine: checks, plan, actions, uninstall, codes",
    "│   ├── ui/           # the text interface (TUI)",
    "│   ├── catalog/   # the catalogue of distributions, desktops and GPUs",
    "│   └── vendor/  # the Go dependencies, vendored",
    "├── packaging/  # debian/, rpm/, arch/, engine/ (packages of the installer), release.sh",
    "├── benches/ # the test benches still alive, one prefix per phase (00-…, 01-…, 11-boxes/, 15-suite/, 17-distro/)",
    "├── docs/  # this manual, generated, and its sources (docs/sources/)",
    "├── misure/  # raw measurements kept with the code",
    "├── phases/ # the documents of the phases (one per phase, from 06 to 21)",
    "├── fondamenta/  # the heritage of REMOTIX v1: its C, benches, documents, tools",
    "├── design/   # the logo and the mockups (login page, installer TUI, site)",
    "├── previews/   # screenshots of the installer TUI",
    "├── memoria/  # working notes of the assistants",
    "├── README.md  # the state of the project and where to start reading",
    "├── SPECS.md       # what the product does and does not do",
    "├── RCP.md  # the protocol, written before the code: the referee between page and server",
    "├── DECISIONS.md  # every decision, with date, author and degree of certainty",
    "├── PLAN.md · PHASES.md · MASTERPLAN.md # the plan, the closed phases, what is left for the end",
    "├── LESSONS.md · STUDIES.md # how to measure; the studies of the desktops, the web and xpra",
    "├── CODER.md · REVIEWER.md  # rules for who writes code and for who reviews it",
    "└── LICENSE.md  # the licence (DECISIONS.md §10.39)",
], "«FIG» — The repository's folders") + \
    table(["Path", "Contents"], [
        [c("src/"), "The product. Every " + c(".c") + "/" + c(".h") + " pair is one module; " + c("page.html")
         + " is the client; " + c("remotix.pam") + ", " + c("remotix.pam.fedora") + ", " + c("remotix.pam.suse")
         + " and " + c("remotix.pam.arch") + " are the PAM stacks per family. " + c("provision.sh") + ", "
         + c("restart-7700.sh") + " and " + c("restart-7900.sh") + " prepare the test machine and restart a "
         "server there as a transient system unit; they are not installed."],
        [c("src/build-targets/"), "One " + c("Containerfile") + " (container) recipe per distribution (Debian 13, Ubuntu 24.04 and "
         "26.04, Fedora 44, Alma 10, Leap 16, Tumbleweed, Arch), " + c("build-all.sh") + ", "
         + c("build-deb.sh") + " and " + c("quic-static.sh") + ", which builds ngtcp2 and nghttp3 as static "
         "libraries because almost no distribution ships the version needed."],
        [c("installer/"), "The installer: " + c("engine/") + " (the engine), " + c("ui/")
         + " (TUI), " + c("catalog/") + " (" + c("catalog.json") + "), " + c("tests/") + " (its own tests), "
         + c("run.sh") + " (the self-extracting " + c(".run") + ")."],
        [c("packaging/"), "The " + c(".deb") + ", " + c(".rpm") + " and Arch recipes, the systemd unit, "
         + c("tmpfiles") + ", firewall descriptions, the disabled belts, the packages of the installer itself, the "
         "release script, the third-party licence tools (" + c("archive/") + ") and, in " + c("labwc-ospite/") + ", the "
         "recipe, the patch and the pinned sources (sha256) of the labwc that hosts KWin 6.5 or later."],
        [c("benches/"), "About 350 files: one script or folder per bench, named after the phase that wrote it. The "
         "benches of closed phases and those that can no longer run left the tree on 10 and 11 October 2026 "
         "(DECISIONS.md §10.44); their measurements stay where they were recorded, the files in git history. "
         + c("benches/rcp/") + " is a twin copy of the RCP code used by the early benches; " + c("benches/prodotto/")
         + " starts and probes the real server in a container."],
        [c("docs/"), "The generated HTML manual and " + c("docs/sources/") + ": " + c("build.py") + ", "
         + c("style.css") + ", " + c("manual.js") + " and one Python file per chapter in " + c("technical/")
         + ". Never edit the HTML by hand."],
        [c("fondamenta/"), "REMOTIX v1 (" + c("remotix-c/") + ", " + c("remotix-rust/") + "), its benches and "
         "documents. Two things in it are still alive: " + c("fondamenta/banco/enter.sh") + " and "
         + c("fondamenta/strumenti/sshpw.py") + ", used by the benches to reach the test machine."],
        [c("phases/"), "The document of each phase from 06 on: what was planned, measured and decided. Older phases "
         "are sewn into " + c("PHASES.md") + "."],
        [c("misure/"), "Raw data of measurement campaigns (phase 16 stress, phase 19 NVIDIA)."],
        [c("design/"), "The official logo (" + c("design/logo/") + ", embedded in this manual's cover) and the "
         "mockups of the login page, the installer and the site."],
        [c("licenses/"), "A page describing the licensing system that was designed and then dropped on 10 October "
         "2026 (DECISIONS.md §10.33): history only."],
    ], "«TAB» — What is in the repository") + \
    warn("several documents carry a status box at the top that was true on the day it was written: "
         + c("README.md") + " still describes " + c("src/") + " as “not in git” and the project as paused, and "
         "the comment at the top of " + c("main.c") + " still says “phase 1, no video”. The code and the newest "
         "sections of " + c("DECISIONS.md") + " win; " + rif("Conventions") + " explains how the documents are "
         "kept.", "Old headers.")

PARTS = [
    ("Server", c("src/*.c") + ", " + c("src/*.h"),
     "parent, children, transport, RCP, capture, encoding, input, audio, clipboard, desktops",
     lambda f: f.startswith("src/") and f.count("/") == 1 and f.endswith((".c", ".h")) and not f.endswith("_spv.h")),
    ("GPU shader", c("vulkanvideo_rgb_nv12.comp") + " and its SPIR-V header",
     "the RGB to NV12 conversion for Vulkan Video; the header is generated from the shader",
     lambda f: f.startswith("src/vulkanvideo_rgb_nv12")),
    ("Wayland protocols", c("src/protocols/"),
     "upstream XML definitions (wlroots, KDE, data control) the server is built against",
     lambda f: f.startswith("src/protocols/")),
    ("The page", c("src/page.html"), "the whole browser client: HTML, CSS and JavaScript in one file",
     lambda f: f == "src/page.html"),
    ("Opus in WebAssembly", c("src/opus-wasm/"), "the page's audio decoder: C source, build script, check",
     lambda f: f.startswith("src/opus-wasm/")),
    ("Build and system files", c("src/Makefile") + ", " + c("src/build-targets/") + ", PAM, polkit and logind files, "
     "test-machine scripts", "how the server is built, and what it installs around itself",
     lambda f: f.startswith("src/")),
    ("Installer (Go)", c("installer/**/*.go"), "engine, TUI, catalogue code, tests",
     lambda f: f.startswith("installer/") and f.endswith(".go")),
    ("Installer data and scripts", c("catalog.json") + ", " + c("run.sh") + ", " + c("build.sh") + ", "
     + c("tests/"), "the catalogue, the self-extracting archive, the installer's own test scripts",
     lambda f: f.startswith("installer/")),
    ("Packaging", c("packaging/"), "deb, rpm and Arch recipes, unit, tmpfiles, release",
     lambda f: f.startswith("packaging/")),
    ("Manual sources", c("docs/sources/"), "this manual's generator, style and chapters",
     lambda f: True),
]

S5 = p("How big REMOTIX is, part by part. The lines are counted from the sources every time the manual is generated: "
       "files kept by git under " + c("src/") + ", " + c("installer/") + " and " + c("packaging/")
       + ", plus the manual's own sources; the vendored Go modules, the protocol headers generated at build time and "
       "binary files are left out. The test benches (" + c("benches/") + ", about 350 files) are not counted.",
       lead=True) + numeri(PARTS, "«TAB» — The project's parts and their line counts") + \
    p("A large share of the C is comment: by the project's rules every non-obvious line carries the reason, the "
      "measurement or the decision behind it, often with the date. The counts in this table and in the file map "
      "are never written by hand.")

CHAPTER = ("Introduction and concepts", [
    ("What REMOTIX is", S1),
    ("Basic concepts", S2),
    ("Subsystems at a glance", S3),
    ("The repository", S4),
    ("The project in numbers", S5),
])
