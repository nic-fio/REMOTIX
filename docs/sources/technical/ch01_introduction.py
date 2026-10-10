from build import VERSION, arrow, box, path, c, conta, dl, fig, note, numeri, p, righe, rif, table, text, tree, warn, zone

INSIEME = fig(
    zone(20, 12, 250, 250, "Any device (a browser)")
    + box(40, 46, 210, 54, "The page", "src/pagina.html, served by the server", "navy")
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
       "browser with WebTransport and WebCodecs is the client. " + c("SPECIFICHE.md") + " says what the product "
       "promises, " + c("RCP.md") + " defines the protocol, " + c("DECISIONI.md") + " records why; this manual "
       "explains how the code does it.", lead=True) + INSIEME + \
    p("Every user who logs in gets <b>their own graphical session</b> on the machine — GNOME, KDE Plasma, XFCE or "
      "LXQt, whichever desktop the machine has — started headless by REMOTIX, with one virtual monitor as large as "
      "the browser window. The session belongs to the user, not to the connection: closing the tab, losing the "
      "network or switching device leaves it running, and the next login finds the same windows. Only the user ends "
      "it, with “Log out” from the desktop menu or " + c("Ctrl+Alt+End") + " in the page, or the server closes it "
      "after 60 minutes without input.") + \
    p("Several users can work on the same machine at once, each in their own desktop (10 by default, set with "
      + c("--tetto-sessioni") + ", the session cap). The video is encoded only on the graphics card (VA-API on Intel and AMD, Vulkan "
      "Video on AMD and NVIDIA) in H.264 or HEVC; the audio travels as Opus in QUIC datagrams; keyboard, pointer, "
      "touch and the text clipboard travel in both directions.") + \
    table(["Item", "Value"], [
        ["Version", c(VERSION) + " (the one in " + c("packaging/rpm/remotix.spec") + ", shared by all packages)"],
        ["Server", "C (" + c("-std=gnu11") + "), Linux only, systemd, runs as root as " + c("remotix.service")],
        ["Client", "The page " + c("src/pagina.html") + " (HTML and JavaScript in one file), served by the server "
         "itself; a small Opus decoder in WebAssembly (" + c("src/opus-wasm/") + ")"],
        ["Installer", c("remotix-install") + ", in Go 1.25 (" + c("installatore/") + ")"],
        ["Protocol", "RCP/1 over WebTransport, path " + c("/rcp/1") + "; port " + c("7447") + " on TCP (the page) "
         "and on UDP (QUIC)"],
        ["Video", "H.264 and HEVC, negotiated with the browser, encoded only on the GPU (no CPU encoder since 1 Oct "
         "2026, DECISIONI.md §10.27); no ffmpeg"],
        ["Desktops", "GNOME, KDE Plasma, XFCE and LXQt (the last two on the labwc compositor); one desktop per "
         "machine (DECISIONI.md §0.6)"],
        ["Sessions", "Wayland only; X11 applications run through XWayland"],
        ["Size", f"{righe(conta('.c') + conta('.h'))} lines of C, {righe(conta('pagina.html'))} lines of page, "
         f"{righe(conta('.go'))} lines of Go"],
        ["Licence", "Our own text, " + c("LICENSE.md") + " (DECISIONI.md §10.39): free for personal and "
         "non-profit use, source readable, no modifications, no redistribution; not open source"],
    ], "«TAB» — REMOTIX at a glance") + \
    p("<b>Why a protocol of our own, and why a browser.</b> REMOTIX v1 spoke RDP and stopped at its phase 11, after "
      "serving GNOME and KDE: the three walls it hit — the H.264 ceiling, an Android client decoding in software and "
      "the full colour that RDP could not carry — were walls of RDP, not of the problem (DECISIONI.md §1.1). Dropping "
      "Windows as a server removed RDP. On 9 August 2026 the dedicated clients went too (DECISIONI.md §1.6): "
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
        ["Chrome", "Android", "HEVC or H.264", "supported (DECISIONI.md §7.19)"],
        ["Firefox", "Linux", "H.264 (Firefox on Linux does not decode HEVC)", "supported"],
        ["Firefox", "Windows", "—", "never tested: neither supported nor excluded"],
        ["Firefox", "Android", "—", "not supported: it has no WebCodecs (DECISIONI.md §7.18)"],
        ["Safari", "macOS, iOS", "—", "never tested"],
    ], "«TAB» — The browsers, as SPECIFICHE.md §11.5 declares them") + \
    p("<b>What REMOTIX deliberately does not do</b> (SPECIFICHE.md §12): Windows as a server; any application to "
      "install on the client; X11 desktop sessions; redirection of disks, printers, serial ports or smart cards; "
      "file transfer; images and files in the clipboard (text only); multi-monitor as a feature; stylus pressure "
      "and tilt; native multi-finger touch (a place is reserved in the protocol); recording the session to a file; "
      "compatibility with RDP, VNC or SPICE clients.") + \
    note("SPECIFICHE.md §3 sets a minimum of 480p, 25 fps, 24 bit, a desired 4K, 60 fps, 10 bit per channel, and a "
         "delay of at most 50 ms (target 40 ms) from the input arriving to the frame leaving. Since 30 September "
         "2026 these are <b>design goals, not measured promises</b> (user decision): performance tests depend too "
         "much on the hardware. The parameters the product really uses — session cap, clocks, ban, minimum "
         "bandwidth — are configuration and hold as written.", "Goals, not promises.")

S2 = p("A few concepts recur in every chapter. Most of them have an Italian name in the code, which the manual "
       "keeps inside code spans so that it can be searched for.", lead=True) + \
    table(["Concept", "What it is", "In the code", "More"], [
        ["<b>Server</b> (the parent)", "The process started by systemd, as root, one per machine: it listens on the "
         "two ports, speaks TLS, QUIC and RCP, and owns every connection. It never touches GLib, PipeWire or D-Bus "
         "of a user", c("main.c"), rif("The parent process")],
        ["<b>PAM helper</b>", "A dispatcher process started at boot, which forks one short-lived process per "
         "password check, so that PAM never blocks the server's loop", c("aiutante.c") + ", "
         + c("autenticazione.c"), rif("The PAM helper process")],
        ["<b>Child</b> (" + c("figlio") + ")", "One process per admitted user, running as that user: it opens the "
         "user's logind session, starts the desktop and holds capture, encoding, input, audio and clipboard. In "
         + c("ps") + " it appears as " + c("remotix-figlio --figlio-interno"), c("figlio.c"),
         rif("The per-user child process")],
        ["<b>Stage</b> (" + c("palco") + ")", "What the child mounts on the user's desktop: the virtual monitor, the "
         "capture stream, the input channel, the clipboard and the cursor. It belongs to the session, not to the "
         "connection (invariant I4)", c("prendi_il_palco()") + " (take the stage)", rif("The stage and the virtual monitor")],
        ["<b>Graphical session</b>", "The user's desktop, started by the child with " + c("setsid --fork")
         + " inside the user's logind session and therefore outside the service's unit", c("sessione.c"),
         rif("Birth of a session")],
        ["<b>Canvas</b> (" + c("tela") + ")", "The size of the remote desktop: the browser window's size at attach "
         "time, at most 4096×2304; it does not change while the client stays", c("ATTACCA") + " (attach), " + c("TELA"),
         rif("The RCP/1 protocol")],
        ["<b>View</b> (" + c("vista") + ")", "The size at which the page draws the canvas; it follows the window "
         "without touching the desktop", c("VISTA"), rif("The browser page")],
        ["<b>Tenant</b> (" + c("inquilino") + ")", "A user being served. The cap (" + c("--tetto-sessioni")
         + ", 10) counts stages, not connections", c("rcp_tetto()"), rif("Where state lives")],
        ["<b>Attach slot</b> (" + c("posto") + ")", "The place of a user's connection in RCP's registry: one per "
         "user; freed when the client detaches or falls silent for 30 s", c("rcp.c"), rif("Detach and reattach")],
        ["<b>Farewell</b> (" + c("CONGEDO") + ")", "The message that closes an RCP session, always with a reason "
         "code and a sentence: the server never closes without saying why (DECISIONI.md §4.1-bis)", c("rcp.h"),
         rif("The RCP/1 protocol")],
        ["<b>Sentinel</b> (" + c("sentinella") + ")", "The code that asks logind whether a user has a local "
         "graphical session, and checks that the remote one has no seat and cannot power the machine off",
         c("sentinella.c"), rif("The logind sentinel")],
        ["<b>Found-again desktops</b>", "Desktops left alive by a previous server process (after a restart or an "
         "upgrade), found at startup and counted until their user comes back", c("ritrovo.c"),
         rif("Desktops found again after a restart")],
        ["<b>Budget</b>", "An optional admission check in megapixels per second of composition; off by default",
         c("budget.c"), rif("Quality, degradation and budget")],
        ["<b>Belts</b> (" + c("cinture") + ")", "The three system settings that forbid power-off, reboot and "
         "suspend to every user: a polkit rule, logind settings for the power key and lid, and sleep settings. "
         "The packages ship them disabled", c("remotix-niente-spegnimento.rules") + " (no power-off)",
         rif("Files on the machine")],
    ], "«TAB» — Basic concepts") + \
    p("The design is held together by eight <b>invariants</b>, numbered in " + c("CODER.md") + " §2 and quoted "
      "throughout the code comments as I1…I8; they are listed in " + rif("Architectural principles") + ".") + \
    note("REMOTIX recognises the desktop from what is installed (" + c("riconosci_desktop()") + " looks for "
         + c("gnome-session") + ", " + c("startplasma-wayland") + ", " + c("xfce4-session") + " and "
         + c("lxqt-session") + " in the " + c("PATH") + "). Machines with more than one desktop are out of scope "
         "(DECISIONI.md §0.6): if two are present, one is chosen — GNOME before KDE, XFCE before LXQt — and the "
         "ambiguity is written in the log at startup.", "One desktop per machine.")

S3 = p("The server's code is split by job. This is the map the manual follows chapter by chapter; the line counts "
       "of every file are in the file map appendix.", lead=True) + dl([
    (c("main.c") + ", " + c("figlio.c") + ", " + c("aiutante.c") + ", " + c("sentinella.c") + ", "
     + c("ritrovo.c") + ", " + c("comando.c"),
     "The processes, the main loop, the birth and death of children, the unblock socket ("
     + rif("Overall architecture") + ", " + rif("Startup and life cycle") + ")."),
    (c("trasporto.c") + ", " + c("webtransport.c") + ", " + c("tls.c") + ", " + c("certificati.c") + ", "
     + c("pagina.c"),
     "UDP and QUIC with ngtcp2 and nghttp3, the WebTransport sessions, the two certificates, the page served over "
     "TCP (" + rif("Transport: QUIC, HTTP/3, WebTransport") + ")."),
    (c("rcp.c") + ", " + c("rcp.h") + ", " + c("autenticazione.c"),
     "The RCP/1 state machine: handshake, credentials, ban, attach, channels, farewell ("
     + rif("The RCP/1 protocol") + ")."),
    (c("mutter.c") + ", " + c("kwin.c") + ", " + c("wlroots.c") + ", " + c("cattura.c") + ", " + c("cursore.c")
     + ", " + c("forma.c"),
     "The virtual monitor and the capture on Mutter, KWin and labwc, PipeWire, dmabuf, the cursor ("
     + rif("Screen capture per compositor") + ")."),
    (c("codificatore.c") + ", " + c("vadiretta.c") + ", " + c("vulkanvideo.c") + ", " + c("colori709.c") + ", "
     + c("scrittore_bit.c"),
     "VA-API and Vulkan Video encoding, BT.709 conversion, the bitstream headers written by hand ("
     + rif("Video encoding") + ")."),
    (c("budget.c") + " and the pacing code in " + c("webtransport.c"),
     "Rate control, behaviour on bad networks, the multi-tenant budget (" + rif("Quality, degradation and budget")
     + ")."),
    (c("pagina.html"), "The whole client: login, WebTransport, WebCodecs decoding, drawing, input, audio, "
     "clipboard (" + rif("The browser page") + ")."),
    (c("input.c") + ", " + c("wlr_input.c") + ", " + c("tastiera.c"),
     "Keyboard, layouts, pointer, wheel and touch injected through libei or the wlroots virtual devices ("
     + rif("Input") + ")."),
    (c("audio.c") + ", " + c("suono.c") + ", " + c("appunti.c") + ", " + c("appunti_kde.c"),
     "The PipeWire sink, Opus, and the clipboard on each desktop (" + rif("Audio and clipboard") + ")."),
    (c("sessione.c"), "How each of the four desktops is born, configured, inhibited and ended ("
     + rif("The four desktops") + ")."),
    (c("registro.c"), "The log, on standard error and in the systemd journal (" + rif("Logging and diagnostics")
     + ")."),
    (c("remotix.pam") + " and its variants, " + c("remotix-niente-spegnimento.rules") + ", "
     + c("remotix-tasti.conf"),
     "PAM stacks per distribution family and the belts (" + rif("Security model") + ")."),
    (c("installatore/"), "The " + c("remotix-install") + " engine, its catalogue and its TUI ("
     + rif("The installer") + ")."),
    (c("banchi/"), "The test benches: the safety net, the functional suite, stress, the distribution boxes ("
     + rif("Testing") + ")."),
    (c("src/Makefile") + ", " + c("src/costruzione/") + ", " + c("packaging/"),
     "Building in containers, the deb, rpm and Arch packages, the release (" + rif("Build and release") + ")."),
])

S4 = p("The " + c("nic-fio/REMOTIX") + " repository on GitHub (private) holds everything: the product, the "
       "installer, the packages, the test benches, the measurements and the documents. Documents and code comments "
       "are in Italian; this manual is in English, and so is most of the page the user sees — but some of the "
       "sentences the page shows, such as the reasons of a farewell (" + c("MOTIVO") + " in " + c("pagina.html")
       + ") and the ban notice, are still in Italian.", lead=True) + tree([
    "REMOTIX/",
    "├── src/  # the product: the server in C, the page, PAM files, build scripts",
    "│   ├── protocolli/  # the Wayland protocol XML files the server is built against",
    "│   ├── costruzione/  # one container recipe per distribution, and the static QUIC libraries",
    "│   └── opus-wasm/  # the page's Opus decoder in WebAssembly, with its check",
    "├── installatore/  # remotix-install, in Go",
    "│   ├── cmd/remotix-install/  # main",
    "│   ├── motore/  # the engine: checks, plan, actions, uninstall, codes",
    "│   ├── interfaccia/  # the text interface (TUI)",
    "│   ├── catalogo/  # the catalogue of distributions, desktops and GPUs",
    "│   └── vendor/  # the Go dependencies, vendored",
    "├── packaging/  # debian/, rpm/, arch/, motore/ (packages of the installer), rilascio.sh",
    "├── banchi/  # the test benches, one prefix per phase (00-…, 01-…, 11-scatole/, 15-suite/, 17-distro/)",
    "├── docs/  # this manual, generated, and its sources (docs/sources/)",
    "├── misure/  # raw measurements kept with the code",
    "├── fasi/  # the documents of the phases (one per phase, from 06 to 21)",
    "├── fondamenta/  # the heritage of REMOTIX v1: its C, benches, documents, tools",
    "├── grafica/  # the logo and the mockups (login page, installer TUI, site)",
    "├── anteprime/  # screenshots of the installer TUI",
    "├── memoria/  # working notes of the assistants",
    "├── README.md  # the state of the project and where to start reading",
    "├── SPECIFICHE.md  # what the product does and does not do",
    "├── RCP.md  # the protocol, written before the code: the referee between page and server",
    "├── DECISIONI.md  # every decision, with date, author and degree of certainty",
    "├── PIANO.md · FASI.md · MASTERPLAN.md  # the plan, the closed phases, what is left for the end",
    "├── LEZIONI.md · STUDI.md  # how to measure; the studies of the desktops, the web and xpra",
    "├── CODER.md · REVIEWER.md  # rules for who writes code and for who reviews it",
    "└── LICENSE.md  # the licence (DECISIONI.md §10.39)",
], "«FIG» — The repository's folders") + \
    table(["Path", "Contents"], [
        [c("src/"), "The product. Every " + c(".c") + "/" + c(".h") + " pair is one module; " + c("pagina.html")
         + " is the client; " + c("remotix.pam") + ", " + c("remotix.pam.fedora") + ", " + c("remotix.pam.suse")
         + " and " + c("remotix.pam.arch") + " are the PAM stacks per family. " + c("provisiona.sh") + ", "
         + c("riavvia-7700.sh") + " and " + c("riavvia-7900.sh") + " prepare the test machine and restart a "
         "server there as a transient system unit; they are not installed."],
        [c("src/costruzione/"), "One " + c("Contenitore") + " (container) recipe per distribution (Debian 13, Ubuntu 24.04 and "
         "26.04, Fedora 44, Alma 10, Leap 16, Tumbleweed, Arch), " + c("costruisci-tutti.sh") + ", "
         + c("costruisci-deb.sh") + " and " + c("quic-statiche.sh") + ", which builds ngtcp2 and nghttp3 as static "
         "libraries because almost no distribution ships the version needed."],
        [c("installatore/"), "The installer: " + c("motore/") + " (the engine), " + c("interfaccia/")
         + " (TUI), " + c("catalogo/") + " (" + c("catalogo.json") + "), " + c("prove/") + " (its own tests), "
         + c("run.sh") + " (the self-extracting " + c(".run") + ")."],
        [c("packaging/"), "The " + c(".deb") + ", " + c(".rpm") + " and Arch recipes, the systemd unit, "
         + c("tmpfiles") + ", firewall descriptions, the disabled belts, the packages of the installer itself, the "
         "release script and the third-party licence tools (" + c("archivio/") + ")."],
        [c("banchi/"), "About 1,800 files: one script or folder per bench, named after the phase that wrote it. "
         + c("banchi/rcp/") + " is a twin copy of the RCP code used by the early benches; " + c("banchi/prodotto/")
         + " starts and probes the real server in a container."],
        [c("docs/"), "The generated HTML manual and " + c("docs/sources/") + ": " + c("build.py") + ", "
         + c("style.css") + ", " + c("manual.js") + " and one Python file per chapter in " + c("technical/")
         + ". Never edit the HTML by hand."],
        [c("fondamenta/"), "REMOTIX v1 (" + c("remotix-c/") + ", " + c("remotix-rust/") + "), its benches and "
         "documents. Two things in it are still alive: " + c("fondamenta/banco/enter.sh") + " and "
         + c("fondamenta/strumenti/sshpw.py") + ", used by the benches to reach the test machine."],
        [c("fasi/"), "The document of each phase from 06 on: what was planned, measured and decided. Older phases "
         "are sewn into " + c("FASI.md") + "."],
        [c("misure/"), "Raw data of measurement campaigns (phase 16 stress, phase 19 NVIDIA)."],
        [c("grafica/"), "The official logo (" + c("grafica/logo/") + ", embedded in this manual's cover) and the "
         "mockups of the login page, the installer and the site."],
        [c("licenze/"), "A page describing the licensing system that was designed and then dropped on 10 October "
         "2026 (DECISIONI.md §10.33): history only."],
    ], "«TAB» — What is in the repository") + \
    warn("several documents carry a status box at the top that was true on the day it was written: "
         + c("README.md") + " still describes " + c("src/") + " as “not in git” and the project as paused, and "
         "the comment at the top of " + c("main.c") + " still says “phase 1, no video”. The code and the newest "
         "sections of " + c("DECISIONI.md") + " win; " + rif("Conventions") + " explains how the documents are "
         "kept.", "Old headers.")

PARTI = [
    ("Server", c("src/*.c") + ", " + c("src/*.h"),
     "parent, children, transport, RCP, capture, encoding, input, audio, clipboard, desktops",
     lambda f: f.startswith("src/") and f.count("/") == 1 and f.endswith((".c", ".h")) and not f.endswith("_spv.h")),
    ("GPU shader", c("vulkanvideo_rgb_nv12.comp") + " and its SPIR-V header",
     "the RGB to NV12 conversion for Vulkan Video; the header is generated from the shader",
     lambda f: f.startswith("src/vulkanvideo_rgb_nv12")),
    ("Wayland protocols", c("src/protocolli/"),
     "upstream XML definitions (wlroots, KDE, data control) the server is built against",
     lambda f: f.startswith("src/protocolli/")),
    ("The page", c("src/pagina.html"), "the whole browser client: HTML, CSS and JavaScript in one file",
     lambda f: f == "src/pagina.html"),
    ("Opus in WebAssembly", c("src/opus-wasm/"), "the page's audio decoder: C source, build script, check",
     lambda f: f.startswith("src/opus-wasm/")),
    ("Build and system files", c("src/Makefile") + ", " + c("src/costruzione/") + ", PAM, polkit and logind files, "
     "test-machine scripts", "how the server is built, and what it installs around itself",
     lambda f: f.startswith("src/")),
    ("Installer (Go)", c("installatore/**/*.go"), "engine, TUI, catalogue code, tests",
     lambda f: f.startswith("installatore/") and f.endswith(".go")),
    ("Installer data and scripts", c("catalogo.json") + ", " + c("run.sh") + ", " + c("costruisci.sh") + ", "
     + c("prove/"), "the catalogue, the self-extracting archive, the installer's own test scripts",
     lambda f: f.startswith("installatore/")),
    ("Packaging", c("packaging/"), "deb, rpm and Arch recipes, unit, tmpfiles, release",
     lambda f: f.startswith("packaging/")),
    ("Manual sources", c("docs/sources/"), "this manual's generator, style and chapters",
     lambda f: True),
]

S5 = p("How big REMOTIX is, part by part. The lines are counted from the sources every time the manual is generated: "
       "files kept by git under " + c("src/") + ", " + c("installatore/") + " and " + c("packaging/")
       + ", plus the manual's own sources; the vendored Go modules, the protocol headers generated at build time and "
       "binary files are left out. The test benches (" + c("banchi/") + ", about 1,800 files) are not counted.",
       lead=True) + numeri(PARTI, "«TAB» — The project's parts and their line counts") + \
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
