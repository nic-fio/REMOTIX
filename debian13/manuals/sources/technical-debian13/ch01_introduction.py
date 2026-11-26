from build import VERSION, arrow, box, c, conta, fig, note, numeri, p, righe, rif, sysf, table, tree, warn, zone

OVERVIEW = fig(
    zone(20, 12, 250, 250, "Any device (a browser)")
    + box(40, 46, 210, 54, "The page", "src/page.html, served by the server", "navy")
    + box(40, 116, 210, 54, "WebCodecs + canvas", "decodes and draws the video", "blue")
    + box(40, 186, 210, 54, "WebTransport", "RCP/1 on HTTP/3", "dark")
    + zone(330, 12, 550, 250, "The Debian 13 machine")
    + box(350, 46, 230, 54, "Root side", "root: PAM, births, the walls", "navy")
    + box(350, 116, 230, 54, "Network side", "user remotix: TLS, QUIC, RCP", "navy")
    + box(350, 186, 230, 54, "logind", "sessions, seats, power", "grey")
    + box(630, 46, 230, 54, "Child of user A", "runs as A: capture, encoding", "blue")
    + box(630, 116, 230, 54, "Child of user B", "runs as B", "blue")
    + box(630, 186, 230, 54, "Desktops of A and B", "GNOME, KDE, XFCE or LXQt", "light")
    + arrow(252, 143, 348, 143, "#0050C0", False, "TCP + UDP 7447", 300, 134)
    + arrow(465, 102, 465, 114, "#475569") + arrow(582, 73, 628, 73) + arrow(582, 143, 628, 133, "#475569", True)
    + arrow(745, 172, 745, 184, "#475569"),
    900, 270, "«FIG» — REMOTIX: a page in the browser, two server processes and one child process per user on the Debian machine")

S1 = p("<b>REMOTIX</b> is the Linux desktop in the browser, for several users at once. A server runs on the machine "
       "and serves one web page; the page and the server talk a protocol of their own, <b>RCP/1</b> (Remotix Control "
       "Protocol), over WebTransport, that is HTTP/3 on QUIC. Nothing is installed on the device the user connects "
       "from: a browser with WebTransport and WebCodecs is the client. The user types the Linux user name and "
       "password of the machine, the server checks them with PAM, and the page shows that user's own desktop. "
       "This manual describes version " + c(VERSION) + ", built from one codebase for one distribution, Debian 13 "
       "(trixie). Each distribution that REMOTIX will serve gets its own manual with the same table of contents.",
       lead=True) + OVERVIEW + \
    p("<b>What the product promises is written elsewhere and is not repeated here.</b> " + c("docs/SPECS.md")
      + " says what REMOTIX does and does not do, in the owner's terms; " + c("docs/RCP.md") + " is the protocol, "
      "byte by byte, and is the referee between the page and the server; " + c("docs/DECISIONS.md") + " and "
      + c("docs/DECISIONS-11.md") + " give the reason and the date of every choice, quoted in this manual as "
      "“DECISIONS §n”. This manual says <i>how the code keeps those promises</i>: which file, which function, which "
      "number, and what has been checked.") + \
    table(["Item", "Value"], [
        ["Version", c(VERSION) + ", from " + c("RX_VERSION") + " in " + c("build/build-deb.sh")],
        ["Server", "C (" + c("-std=gnu11") + "), Linux only, systemd, one server executable " + c("/usr/libexec/remotix/remotix")
         + " started by " + c("remotix.service") + " as root; it re-executes itself for the network side, the PAM "
         "helper and the per-user children (" + rif("Overall architecture") + "). The package also ships a second, very small "
         "program, " + c("remotix-local-login") + ", that PAM runs at a local login (" + rif("The local-login hold") + "), and a shell script, "
         + c("remotix-pam-hook") + ", that the unit runs before every start to check that the line of that hook is still in " + sysf("/etc/pam.d/common-session") + " (" + rif("Startup and life cycle") + ")"],
        ["Client", "The page " + c("src/page.html") + " (HTML and JavaScript in one file), served by the server itself "
         "over TCP; a small Opus decoder in WebAssembly (" + c("src/opus-wasm/") + ")"],
        ["Protocol", "RCP/1 over WebTransport, path " + c("/rcp/1") + "; port " + c("7447") + " (" + c("DEFAULT_PORT")
         + " in " + c("main.c") + "), TCP for the page and UDP for QUIC"],
        ["Video", "H.264 and HEVC, negotiated with the browser, encoded only on the graphics card (VA-API, Vulkan "
         "Video); with no card that encodes, the server offers no codec and says why (DECISIONS §10.27)"],
        ["Audio and clipboard", "Opus in QUIC datagrams; text clipboard in both directions"],
        ["Desktops", "GNOME, KDE Plasma, XFCE and LXQt, Wayland only; X11 programs run through XWayland. One desktop "
         "per machine is recognised at startup (" + c("session_desktop_explain()") + ")"],
        ["Users", "Several at once, one desktop each; the session cap is " + c("RCP_SESSION_CAP") + " = 10 in "
         + c("rcp.h") + ", moved by " + c("--session-cap") + ". The <b>declared</b> limits of the product (owner's decision, "
         + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026) are <b>8 users</b> at the same time and resolution up to <b>3K</b> "
         "(the size actually used depends on the client); the technical bounds are higher (a protocol canvas of 4096×2304)"],
        ["Clocks", "30 s of client silence (" + c("SILENCE") + " in " + c("rcp.c") + "), 30 min without input "
         "(" + c("DEFAULT_INACTIVITY") + " in " + c("rcp.c") + "), 60 min until the session is closed (" + c("DEFAULT_ABANDON_MS")
         + " in " + c("main.c") + "); see " + rif("Startup and life cycle")],
        ["Packaging", "A single " + c(".deb") + " built in a Debian 13 virtual machine, with no container (" + c("build/build-deb-vm.sh") + ", " + rif("Build and release")
         + "); the service is installed disabled and not started (" + rif("The package") + "). The package carries its own AppArmor profile for the network side, a " + c("needrestart")
         + " rule that keeps the service from being restarted by an update, and the " + c("pam-auth-update") + " profile of the local-login hook"],
        ["Size", f"{righe(conta('.c') + conta('.h'))} lines of C and headers, {righe(conta('page.html'))} lines of page "
         "(counted when the manual is generated)"],
        ["Licence", "A licence text of the author, " + c("LICENSE.md") + ", shipped in the package with "
         + c("THIRD-PARTY-LICENSES") + "; not an open-source licence for REMOTIX. The package carries no third-party program: ngtcp2 and nghttp3 are linked into the "
         "server statically, and the " + c("labwc") + " that XFCE and LXQt use (and that hosts KWin on KDE) is Debian's own package, not a part of REMOTIX's; "
         "there is no wlroots in it and no installer. " + c("THIRD-PARTY-LICENSES") + " lists ngtcp2 1.25.0, nghttp3 1.18.0 (with sfparse), libopus 1.5.2 "
         "(WebAssembly, inside the page), the Emscripten system libraries (with musl) and 10 Wayland protocol files"],
    ], "«TAB» — REMOTIX at a glance") + \
    note("SPECS §3 gives targets of image quality, frame rate and delay (a minimum of 480p at 25 fps, a desired 4K at "
         "60 fps, a delay of at most 50 ms). Since 30 September 2026 they are <b>design goals, not measured promises</b> "
         "(owner's decision recorded in SPECS §3): performance depends on the hardware. The parameters the product really "
         "enforces (session cap, clocks, ban, minimum bandwidth) are configuration and hold as written.",
         "Goals, not promises.")

S2 = p("Two kinds of statement are made in this manual and they are kept apart. What was <b>verified</b> was run "
       "on the owner's development server, in four virtual machines (one per desktop, with a graphics card passed through to the one "
       "being tested) with real browsers, by the checks in " + c("prove/") + " (" + rif("Testing") + "), and in a Debian 13 virtual machine "
       "for the package. What was <b>not verified</b> is said every time it matters, and collected in "
       + rif("Appendix C — Known issues and open points") + ".", lead=True) + \
    table(["Area", "Verified (PIANO.md)", "Not verified"], [
        ["Desktops", "XFCE, LXQt, KDE Plasma and GNOME, each by " + c("prove/all.sh") + " in its own virtual machine; the lines that do not "
         "pass are listed in PIANO.md", "Four desktops on one machine together; a desktop on the physical "
         "display; the local login that closes the remote desktop <i>with programs open</i> was run on GNOME on the bench and, "
         "on the four desktops, by the owner from the live images"],
        ["Browsers", "Chrome and Firefox on Linux (base, input, audio); Chrome for the clipboard; the owner's own test "
         "with Samsung DeX on GNOME (clipboard, audio and video, window resizing)", "Firefox clipboard (open); a real "
         "phone; Safari; Firefox on Windows and Android"],
        ["Life cycle", "Reattach (clean close, killed browser, other window size), Log Out, restart of the service, "
         "network drop, simultaneous entries of one user, one user leaving while another works, the three clocks at "
         "short values (" + c("prove/check-lifecycle.py") + ", " + c("prove/check-resilience.py") + "); the local-login hold "
         "(" + c("prove/check-prelocal.py") + ", the login simulated)",
         "The 30-min and 60-min clocks at their real values (only the mechanism at short values)"],
        ["Package", "Installation, restart, removal and purge on a real Debian 13 VM; AppArmor profile in complain and "
         "enforce mode with no denial up to the connection", "A session under the AppArmor profile on a machine with "
         "a graphics card (the profile is still in complain mode); a card that is not an AMD or Intel one (NVIDIA: measured on Ubuntu 26.04 on 5–6 Oct 2026, "
         "with an earlier version of the code; not run again on Debian 13); a 4096×2304 canvas"],
    ], "«TAB» — What has been checked, and where the checking stops") + \
    p("<b>Browsers as SPECS §11.5 declares them.</b> Chrome and the other Blink browsers on Linux and Windows: HEVC "
      "if the device decodes it, otherwise H.264. Chrome on Android: HEVC or H.264. Firefox on Linux: H.264 only. "
      "Firefox on Windows and Safari were never tested; Firefox on Android is outside the project (no WebCodecs). "
      "The technical minimum is WebTransport and WebCodecs.") + \
    p("<b>What REMOTIX deliberately does not do</b> (SPECS §12): Windows as a server; any program to install on the "
      "client; X11 desktop sessions; redirection of disks, printers, serial ports or smart cards; file transfer; "
      "images or files in the clipboard; multi-monitor as a feature; stylus pressure and tilt; native multi-finger touch; "
      "recording a session; compatibility with RDP, VNC or SPICE clients.") + \
    warn("The specification documents carry the history of the project and are not always rewritten when a decision "
         "changes. Where the code and a document disagree, this manual follows the code and records the difference "
         "(" + rif("Appendix C — Known issues and open points") + "). Two examples: SPECS §5.2-bis and §7.3-bis still "
         "describe the " + c("Ctrl+Alt+End") + " logout shortcut and the " + c("Ctrl+Alt+Del") + " button, removed in August 2026; "
         "and the documents cite files of the old repository (" + sysf("CODER.md") + ", " + sysf("STUDIES.md")
         + ", " + sysf("PHASES.md") + ") that are not in this tree.", "Documents and code.")

S3 = p("A handful of words recur in every chapter. Their names in the code are in code spans, so that they can be "
       "searched for. Identifiers, options and log text are in English; a few source files and symbols keep Italian "
       "names (for example " + c("registro_dice()") + ", the log function) and are quoted as they are.", lead=True) + \
    table(["Word", "What it is", "In the code", "More"], [
        ["<b>Root side</b>", "The process systemd starts, as root, one per machine. It binds the port, probes the graphics "
         "card, runs the PAM helper, forks the network side and the per-user children, and keeps the closed list of "
         "requests the network side may make of it", c("rootside.c") + ", " + c("rootside_proto.h"),
         rif("Overall architecture")],
        ["<b>Network side</b>", "The same binary re-executed as the system user " + c("remotix") + " behind the walls: "
         "it holds the TLS key, speaks QUIC, WebTransport and RCP, serves the page and never forks. If a bug in these "
         "parsers lets a stranger run code, the code is in a room with no doors", c("main.c") + ", " + c("walls.c"),
         rif("Security model")],
        ["<b>PAM helper</b>", "A dispatcher forked by the root side that forks one short-lived process per password check, "
         "so that PAM never blocks a loop and is never used twice in one process", c("helper.c") + ", "
         + c("authentication.c"), rif("Login and its defences")],
        ["<b>Child</b>", "One process per admitted user, running as that user: it opens the user's logind session, starts "
         "the desktop and holds capture, encoding, input, audio and clipboard. It appears in " + c("ps")
         + " as " + c("remotix-child"), c("child.c"), rif("Startup and life cycle")],
        ["<b>Stage</b>", "What the child mounts on the user's desktop: the virtual monitor, the capture stream, the input "
         "channel, the clipboard. It belongs to the session, not to the connection (invariant I4)", c("take_stage()"),
         rif("Screen capture")],
        ["<b>Canvas, view</b>", "The canvas is the size of the remote desktop, fixed at attach to the browser window "
         "(at most 4096×2304 on the protocol; the declared limit is 3K); the view is the size at which the page draws it", c("CANVAS") + ", " + c("VIEW"),
         rif("The RCP/1 protocol")],
        ["<b>Attach slot</b>", "The place of a user's live connection in RCP's registry: one per user; freed when the "
         "client detaches or is silent for 30 s", c("struct slot") + " in " + c("rcp.c"), rif("The RCP/1 protocol")],
        ["<b>Farewell</b>", c("FAREWELL") + ": the message that closes an RCP session, always with a reason code and a "
         "sentence; the server never closes without saying why", c("rcp.h"), rif("The RCP/1 protocol")],
        ["<b>Sentinel</b>", "The code that asks logind whether a user has a local graphical session, and whether the "
         "remote one has no seat", c("sentinel.c"), rif("Security model")],
        ["<b>Found again</b>", "A desktop with no child whose user returns within the few seconds before the root side ends it "
         "(“no orphan desktops”); after an orderly stop there is none", c("rediscover.c"), rif("Startup and life cycle")],
        ["<b>Belts</b>", "The three settings that forbid power-off, reboot and suspend to every user: a polkit rule, "
         "logind settings for the power key and lid, and sleep settings", c("remotix-no-poweroff.rules"),
         rif("Security model")],
        ["<b>Budget</b>", "An optional admission check in megapixels per second; off by default", c("budget.c"),
         rif("Quality, degradation and budget")],
    ], "«TAB» — Basic vocabulary") + \
    p("<b>Seven invariants</b> are quoted in code comments as I1…I7. Their full text is in " + sysf("CODER.md")
      + " of the old repository, which is not in this tree; the table gives them as the code uses them.") + \
    table(["", "Invariant as the code applies it", "Where it shows"], [
        ["I1", "Never close or disconnect out of prudence: a degraded session is worth more than a closed one; a drop in "
         "frame rate happens only on a measurement and is logged", rif("Quality, degradation and budget")],
        ["I2", "One graphical session per user; the local one wins; a second remote connection is refused with a reason",
         c("children_ensure_from()") + " looks before forking; " + c("RCP_ALREADY_ACTIVE_REMOTELY") + " in " + c("rcp.h")],
        ["I3", "The guard starts from “denied”: whoever has not passed the validator gets no pixel and commands nothing",
         "the single byte " + c("1") + " of the PAM helper; kernel credentials on every child message; "
         + c("rootside_check_packet()")],
        ["I4", "The stage belongs to the session, not to the connection, and survives detaching", c("setsid --fork")
         + " in " + c("session.c") + "; no line ties a child to a connection"],
        ["I5", "The volume belongs to the session: a freshly mounted audio path starts audible", c("sound.c")],
        ["I6", "Anything that changes what the user sees stays behind a switch that is off until it has been looked at; "
         "the value in force is written at startup, on and off", "the startup lines of " + c("main.c")],
        ["I7", "The protection against a known defect lives in the program, not in a configuration line that can be lost",
         "the headless and power-off checks the child makes after startup (" + c("sentinel_without_seat()") + ", "
         + c("sentinel_shutdown_forbidden()") + ")"],
    ], "«TAB» — The invariants quoted in the code")

S4 = p("The repository holds the product, the package recipe, the build scripts, the checks that drive real "
       "browsers, the dev-server scripts and the specifications. Everything is in English except part of the "
       "older documents.", lead=True) + tree([
    "REMOTIX-DEBIAN/",
    "├── src/            # the product: the server in C, the page, the PAM file, the polkit rules",
    "│   ├── protocols/  # Wayland protocol XML files the server is built against",
    "│   └── opus-wasm/  # the page's Opus decoder (build script and the .wasm)",
    "├── debian/         # the package: control, rules, unit, maintainer scripts, AppArmor profile",
    "├── build/          # build-deb-vm.sh (the build, on a virtual machine), build-deb.sh (its checks, and the older container build), quic-static.sh",
    "├── prove/          # the checks with real browsers: all.sh and one check-*.py per area",
    "├── boxes/          # the four older test containers, one per desktop (the tests run on virtual machines, prove/banco-vm/)",
    "├── server/         # scripts of the dev server and of the VM login test",
    "├── docs/           # SPECS.md, RCP.md, DECISIONS*.md, LESSONS.md and the cleaning inventories",
    "├── licenses/       # how-it-works.html: history of a licensing system that was dropped",
    "├── manuals/        # this manual and the user manual, generated from manuals/sources/",
    "├── LICENSE.md · THIRD-PARTY-LICENSES",
    "└── CLAUDE.md · PIANO.md   # the working rules and the plan with the current state",
], "«FIG» — The repository's folders") + \
    table(["Path", "Contents"], [
        [c("src/"), "Every " + c(".c") + "/" + c(".h") + " pair is one module; " + c("page.html") + " is the client; "
         + c("remotix.pam") + " is the PAM stack; " + c("remotix-no-poweroff.rules") + ", "
         + c("remotix-remote-sessions.rules") + " and " + c("remotix-polkit-seated") + " are the polkit pieces; "
         + c("remotix-power-keys.conf") + " is a logind belt; " + c("Makefile") + " builds the server."],
        [c("debian/"), c("control") + ", " + c("rules") + ", the unit " + c("remotix.service") + ", "
         + c("remotix.sysusers") + " (the user " + c("remotix") + "), " + c("remotix.tmpfiles") + ", the maintainer scripts, "
         + c("remotix_network.apparmor") + " and " + c("denied-users") + "."],
        [c("build/"), c("build-deb-vm.sh") + " builds the .deb in the " + c("costruzione") + " virtual machine (no container); " + c("build-deb.sh") + " is the older build in a " + c("debian:trixie") + " podman container, kept in the tree; "
         + c("quic-static.sh") + " builds ngtcp2 and nghttp3 as static libraries because Debian does not ship the "
         "versions needed (" + c("src/Makefile") + " lists them)."],
        [c("prove/"), c("all.sh") + " runs, for one desktop, the base, lifecycle, multiuser, desktop, media, resilience, "
         "audio, clipboard, input, phone and ban checks; " + c("check-package.py") + " checks the installed package."],
        [c("boxes/"), "The four containers (XFCE, LXQt, GNOME, KDE) on the dev server, started by " + c("box.sh") + "."],
        [c("docs/"), "Specifications and decisions, and the two cleaning documents: " + c("INVENTARIO-non-debian.md")
         + " (code that exists only for another distribution, still to remove) and " + c("PULIZIA-tranche1.md")
         + " (what the first cleaning removed, with proofs)."],
    ], "«TAB» — What is in the repository") + \
    note("The rules of the working copy are in " + c("CLAUDE.md") + ": Debian 13 only, no distribution detection and no "
         "per-distribution code, builds and tests only on the dev server (never on the tablet), and the old repository "
         "is a read-only reference. A future distribution gets its own, separate code.", "Debian only.")

PARTS = [
    ("Server", c("src/*.c") + ", " + c("src/*.h"),
     "root side, network side, helper, children, transport, RCP, capture, encoding, input, audio, clipboard, desktops",
     lambda f: f.startswith("src/") and f.count("/") == 1 and f.endswith((".c", ".h")) and not f.endswith("_spv.h")),
    ("GPU shader", c("vulkanvideo_rgb_nv12.comp") + " and its SPIR-V header",
     "the RGB to NV12 conversion for Vulkan Video; the header is generated from the shader",
     lambda f: f.startswith("src/vulkanvideo_rgb_nv12")),
    ("Wayland protocols", c("src/protocols/"), "upstream XML definitions the server is built against",
     lambda f: f.startswith("src/protocols/")),
    ("The page", c("src/page.html"), "the whole browser client: HTML, CSS and JavaScript in one file",
     lambda f: f == "src/page.html"),
    ("Other files of src/", c("Makefile") + ", PAM, polkit and logind files, " + c("opus-wasm/build.sh"),
     "how the server is built and what it installs around itself", lambda f: f.startswith("src/")),
    ("Package", c("debian/"), "control, rules, unit, maintainer scripts, AppArmor profile",
     lambda f: f.startswith("debian/")),
    ("Build", c("build/"), "the build on a virtual machine, the older container build, the static QUIC libraries", lambda f: f.startswith("build/")),
    ("Checks and test rigs", c("prove/") + ", " + c("boxes/") + ", " + c("server/"),
     "the checks with real browsers, the virtual-machine bench, the older containers, the dev-server scripts",
     lambda f: f.startswith(("prove/", "boxes/", "server/"))),
    ("Manual sources", c("manuals/sources/"), "this manual's generator, style and chapters", lambda f: True),
]

S5 = p("How big REMOTIX is, part by part. The lines are counted from the sources every time the manual is generated: "
       "the files kept by git under " + c("src/") + ", " + c("debian/") + ", " + c("build/") + ", " + c("prove/") + ", "
       + c("boxes/") + " and " + c("server/") + ", plus the manual's own sources; binary files are left out.",
       lead=True) + numeri(PARTS, "«TAB» — The project's parts and their line counts") + \
    p("A large share of the C is comment: by the project's rules a non-obvious line carries the reason, the measurement "
      "or the decision behind it, often with the date. A comment is not always right: where a comment and the code "
      "disagree this manual follows the code (" + rif("Conventions") + ").")

CHAPTER = ("Introduction and concepts", [
    ("What REMOTIX is and what it promises", S1),
    ("What was verified and what was not", S2),
    ("Basic vocabulary and the invariants", S3),
    ("The repository, folder by folder", S4),
    ("The project in numbers", S5),
])
