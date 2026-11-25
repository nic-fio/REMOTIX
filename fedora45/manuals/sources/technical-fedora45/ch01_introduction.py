from build import VERSION, arrow, box, c, conta, fig, note, numeri, p, righe, rif, sysf, table, tree, ui, warn, zone

OVERVIEW = fig(
    zone(20, 12, 250, 250, "Any device (a browser)")
    + box(40, 46, 210, 54, "The page", "src/page.html, served by the server", "navy")
    + box(40, 116, 210, 54, "WebCodecs + canvas", "decodes and draws the video", "blue")
    + box(40, 186, 210, 54, "WebTransport", "RCP/1 on HTTP/3", "dark")
    + zone(330, 12, 550, 250, "The Fedora 45 machine")
    + box(350, 46, 230, 54, "Root side", "root: PAM, births, the walls", "navy")
    + box(350, 116, 230, 54, "Network side", "user remotix: TLS, QUIC, RCP", "navy")
    + box(350, 186, 230, 54, "logind", "sessions, seats, power", "grey")
    + box(630, 46, 230, 54, "Child of user A", "runs as A: capture, encoding", "blue")
    + box(630, 116, 230, 54, "Child of user B", "runs as B", "blue")
    + box(630, 186, 230, 54, "Desktops of A and B", "GNOME, KDE, XFCE or LXQt", "light")
    + arrow(252, 143, 348, 143, "#0050C0", False, "TCP + UDP 7447", 300, 134)
    + arrow(465, 102, 465, 114, "#475569") + arrow(582, 73, 628, 73) + arrow(582, 143, 628, 133, "#475569", True)
    + arrow(745, 172, 745, 184, "#475569"),
    900, 270, "«FIG» — REMOTIX: a page in the browser, two server processes and one child process per user on the Fedora machine")

S1 = p("<b>REMOTIX</b> is the Linux desktop in the browser, for several users at once. A server runs on the machine "
       "and serves one web page; the page and the server talk a protocol of their own, <b>RCP/1</b> (Remotix Control "
       "Protocol), over WebTransport, that is HTTP/3 on QUIC. Nothing is installed on the device the user connects "
       "from: a browser with WebTransport and WebCodecs is the client. The user types the Linux user name and "
       "password of the machine, the server checks them with PAM, and the page shows that user's own desktop. "
       "This manual describes version " + c(VERSION) + " for <b>Fedora 45</b>, built from the code of the "
       "folder " + c("fedora45/") + ": one codebase and one package for the four desktops of that release, GNOME (Fedora "
       "Workstation), KDE Plasma, XFCE and LXQt. Each distribution that REMOTIX serves has its own manual "
       "with the same table of contents.",
       lead=True) + OVERVIEW + \
    p("<b>What the product promises is written elsewhere and is not repeated here.</b> " + c("docs/SPECS.md")
      + " says what REMOTIX does and does not do, in the owner's terms; " + c("docs/RCP.md") + " is the protocol, "
      "byte by byte, and is the referee between the page and the server; " + c("docs/DECISIONS.md") + " and "
      + c("docs/DECISIONS-11.md") + " give the reason and the date of every choice, quoted in this manual as "
      "“DECISIONS §n”. The decisions taken for Fedora (D1 to D8) are written only in " + c("PIANO.md") + " and are quoted as “PIANO D<i>n</i>”; "
      "the problems met on Fedora are numbered F1 to F36 in " + c("docs/REGISTRO-problemi.md") + " and are quoted as “REGISTRO F<i>n</i>”. This manual says <i>how the code keeps those promises</i>: which file, which function, which "
      "number, and what has been checked.") + \
    table(["Item", "Value"], [
        ["Version", c(VERSION) + ", from the " + c("Version:") + " line of " + c("rpm/remotix.spec") + " (the same line "
         + c("build/build-rpm.sh") + " reads); the package is " + c("remotix-" + VERSION + "-1.fc45.x86_64.rpm")
         + ", installed with " + c("sudo dnf install ./remotix-" + VERSION + "-1.fc45.x86_64.rpm") + " and removed with "
         + c("sudo dnf remove remotix")],
        ["Server", "C (" + c("-std=gnu11") + "), Linux only, systemd, one server executable " + c("/usr/libexec/remotix/remotix")
         + " started by " + c("remotix.service") + " as root; it re-executes itself for the network side, the PAM "
         "helper and the per-user children (" + rif("Overall architecture") + "). The package also ships three small programs: "
         + c("remotix-local-login") + ", that PAM runs at a local login (" + rif("The local-login hold") + "), "
         + c("remotix-pam-hook") + ", a script that puts the line which starts it into the PAM stacks of the login screens "
         "(gdm, plasmalogin, lightdm, sddm), and " + c("remotix-polkit-seated") + ". There is no second compositor: a KDE session "
         "runs on KWin alone (" + rif("The four desktops") + ")"],
        ["Client", "The page " + c("src/page.html") + " (HTML and JavaScript in one file), served by the server itself "
         "over TCP; a small Opus decoder in WebAssembly (" + c("src/opus-wasm/") + ")"],
        ["Protocol", "RCP/1 over WebTransport, path " + c("/rcp/1") + "; port " + c("7447") + " (" + c("DEFAULT_PORT")
         + " in " + c("main.c") + "), TCP for the page and UDP for QUIC"],
        ["Video", "H.264 and HEVC, negotiated with the browser, encoded only on the graphics card (VA-API, Vulkan "
         "Video); with no card that encodes, the server offers no codec and says why (DECISIONS §10.27). <b>On Fedora the "
         "encoder is a requirement the administrator meets</b>: the drivers that encode come from RPM Fusion (PIANO D1; "
         + rif("Requirements and what Fedora adds") + ")"],
        ["Audio and clipboard", "Opus in QUIC datagrams; text clipboard in both directions"],
        ["Desktops", "GNOME 51 (display manager " + c("gdm") + "), KDE Plasma 6.8 (" + c("plasmalogin") + "; KWin 6.8 alone), XFCE 4.20 ("
         + c("lightdm") + ") and LXQt 2.4 (" + c("sddm") + "), Wayland only; X11 programs run through XWayland. XFCE and LXQt "
         "run on the " + c("labwc") + " of Fedora's repositories. One desktop per machine is recognised at startup ("
         + c("session_desktop_explain()") + "). The versions are those measured on the Fedora 45 virtual machines "
         "(" + c("studio/") + " studies 1 to 4)"],
        ["Users", "Several at once, one desktop each; the session cap is " + c("RCP_SESSION_CAP") + " = 10 in "
         + c("rcp.h") + ", moved by " + c("--session-cap") + ". How many users really work together depends on the machine "
         "(video card, processor, memory); the canvas of the protocol is at most 4096×2304 (the size actually used depends on the client)"],
        ["Clocks", "30 s of client silence (" + c("SILENCE") + " in " + c("rcp.c") + "), 30 min without input "
         "(" + c("DEFAULT_INACTIVITY") + " in " + c("rcp.c") + "), 60 min until the session is closed (" + c("DEFAULT_ABANDON_MS")
         + " in " + c("main.c") + "); see " + rif("Startup and life cycle")],
        ["Packaging", "A single " + c(".rpm") + " built on a Fedora 45 virtual machine, with no containers (" + c("build/build-rpm.sh") + "; "
         + rif("Build and release") + "); the service is installed disabled and not started (" + rif("The package")
         + "). The package carries its own SELinux module and a firewalld service definition that it never opens"],
        ["Size", f"{righe(conta('.c') + conta('.h'))} lines of C and headers, {righe(conta('page.html'))} lines of page "
         "(counted when the manual is generated)"],
        ["Licence", "A licence text of the author, " + c("LICENSE.md") + ", shipped in the package with "
         + c("THIRD-PARTY-LICENSES") + "; not an open-source licence for REMOTIX. The package carries no third-party "
         "program, but ngtcp2 and nghttp3 are linked into the server statically: the " + c("labwc") + " that XFCE and LXQt use is Fedora's own package. " + c("THIRD-PARTY-LICENSES")
         + " lists ngtcp2 1.25.0, nghttp3 1.18.0 (with sfparse), libopus 1.5.2 (WebAssembly, inside the page), the Emscripten system libraries (with musl) and 12 Wayland protocol files"],
    ], "«TAB» — REMOTIX at a glance") + \
    note("SPECS §3 gives targets of image quality, frame rate and delay (a minimum of 480p at 25 fps, a desired 4K at "
         "60 fps, a delay of at most 50 ms). Since 30 September 2026 they are <b>design goals, not measured promises</b> "
         "(owner's decision recorded in SPECS §3): performance depends on the hardware. The parameters the product really "
         "enforces (session cap, clocks, ban, minimum bandwidth) are configuration and hold as written.",
         "Goals, not promises.")

S1B = p("What an administrator must have in place before REMOTIX works on Fedora 45, and what is different from the other "
        "distributions. None of it is a surprise at run time: the package says it at installation, and the server says it "
        "in its log.", lead=True) + \
    table(["Item", "What it is on Fedora 45", "Where it comes from"], [
        ["Video encoding on the graphics card (required)",
         "REMOTIX encodes the desktop only on the video card, and Fedora's own Mesa leaves the H.264 and HEVC codecs out. "
         "The administrator enables RPM Fusion (free) and installs " + sysf("mesa-va-drivers-freeworld") + " (NVIDIA: its "
         "proprietary driver). There is no software encoding. Without a codec the server offers none and the browser's "
         "request is answered " + c("NOTHING_IN_COMMON") + " (" + rif("The card that arrives late") + "). The package does not "
         "depend on the drivers; it refuses a first installation on a machine with no render node, and it only warns "
         "(" + c("sudo /usr/libexec/remotix/remotix --encoding-test h264") + ") when the card is there and does not encode",
         "PIANO D1; " + c("rpm/remotix.spec") + " " + c("%pre") + " and " + c("%post")],
        ["SELinux, enforcing",
         "The package ships its own module (" + c("selinux/remotix.te") + "): the root side runs in " + c("remotix_t") + ", the "
         "network side in " + c("remotix_net_t") + ", the hook of the local login in " + c("remotix_hook_t") + ". Nothing "
         "is switched to permissive, and the module is the same wall that AppArmor gives on Debian and Ubuntu (" + rif("The network side and its walls")
         + ")", "PIANO D3; REGISTRO F24"],
        ["Firewall",
         "The package defines the firewalld service " + c("remotix") + " (7447/tcp and 7447/udp) and never opens it. The "
         "administrator does: " + c("sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload")
         + " (add " + c("--zone=NAME") + " for a zone other than the default). There is no ufw",
         "PIANO D5; REGISTRO F20 (" + rif("Listeners, sockets and port 7447") + ")"],
        ["Compositor of XFCE and LXQt",
         "The " + c("labwc") + " of Fedora's repositories (a weak dependency of the package: without it these two desktops "
         "cannot be born, and the installation says so). KDE needs no other compositor: it runs on KWin 6.8 alone",
         "PIANO D2; " + c("rpm/remotix.spec")],
        ["Login screens", "gdm (GNOME), plasmalogin (KDE), lightdm (XFCE) and sddm (LXQt); the hook of the local login "
         "is put in the PAM stack of each (" + rif("The local-login hold") + ")", "PIANO D4; REGISTRO F6, F9, F21"],
        ["Clock of the client device",
         "The certificate of a session starts one hour before it is made. A device whose clock is more than an hour "
         "behind the server's sees the browser say " + ui("Opening handshake failed") + "; the server's log now says why "
         "(" + rif("Why a connection closed") + "). The clock of the client must be right",
         "REGISTRO F23"],
        ["Power-off", "Nobody can power off, reboot or suspend the machine from a desktop, the local user included (the polkit "
         "rule: " + rif("Security model") + ")", "SPECS; unchanged from Debian and Ubuntu"],
    ], "«TAB» — Requirements of Fedora 45 and what Fedora adds") + \
    p("<b>Declared limits.</b> The keyring of the desktop (GNOME's " + c("oo7") + ", KDE's " + c("ksecretd") + ") is not "
      "unlocked by the remote sign-in, as on Debian and Ubuntu; XFCE has no keyring and LXQt none either (studies 3 and 4). The XFCE "
      "desktop has a black background and no icons on the desk, because Fedora's " + c("xfdesktop") + " is built without "
      "Wayland (PIANO D7); no remedy is in the code. An SELinux <i>confined</i> user (" + c("staff_u") + ") gets the same "
      "context as at a local login (REGISTRO F25), and on XFCE the panel of such a user does not start: a limit of Fedora 45, "
      "not of REMOTIX (REGISTRO F30). A local graphical session of the same user closes the remote desktop on the four "
      "desktops (" + rif("Ending a graphical session") + ").")

S2 = p("Two kinds of statement are made in this manual and they are kept apart. What was <b>verified</b> was run by the "
       "checks in " + c("prove/") + " (" + rif("Testing") + ") with real browsers, and by the owner by hand, between 21 and "
       "25 November 2026. What was <b>not verified</b> is said every time it matters, and collected in "
       + rif("Appendix C — Known issues and open points") + ". There are no containers in this work: the checks run on virtual "
       "machines, and the last proofs on a real machine started from a live image. Every figure below is the one written "
       "in " + c("PIANO.md") + " or in " + c("docs/REGISTRO-problemi.md") + ", with its date.",
       lead=True) + \
    table(["Means", "What it is"], [
        ["Test bench", "Five QEMU virtual machines on the dev server, one per desktop (GNOME, KDE, XFCE, LXQt) and one that builds "
         "the package, run by " + c("server/vm-radeon.sh") + "; one Radeon card is passed through, so one machine at a time has it. "
         "Each test machine starts from the snapshot " + c("codec") + " (a clean install with the RPM Fusion codecs). "
         + c("prove/banco-vm/") + " lets the checks of " + c("prove/") + " run on them"],
        ["Package", "Built on the " + c("costruzione") + " virtual machine by " + c("build/build-rpm.sh") + ". The candidate "
         "packages of the work were lettered (" + c("h1") + " for the final round, " + c("i2") + " the last one before the version "
         "number was changed to " + c("1.2.0") + ")"],
        ["Real machine", "The dev server started from the Fedora 45 live image of each desktop; the package installed there by " + c("server/live-installa.sh") + "; the owner's own hand proof"],
    ], "«TAB» — The machines used") + \
    table(["Area", "Verified (PIANO.md and REGISTRO, 21-25 Nov 2026)", "Not verified"], [
        ["Final round on the virtual machines", "Package " + c("h1") + " (23 Nov 2026, SELinux enforcing): as the plan records the result, GNOME 52 "
         "PASS (the one FAIL is the known " + c("pkexec") + " line: the product opens no password window by design) plus 39 PASS of "
         + c("prove/all.sh") + "; KDE 76; XFCE 60; LXQt 60; the negative proof of the wall 0 FAIL; no SELinux denial of the product's own. "
         "The package " + c("i2") + ", the candidate, was run on KDE only (" + c("check-prelocal.py") + " P1 to P8 PASS and a short "
         "round); the owner decided that it would not be rerun on the other three, because it differs from " + c("h1")
         + " only in the KDE close and one SELinux rule"],
        ["Owner's hand proof, virtual machines", "23 Nov 2026: all four desktops with " + c("h1") + " and the SELinux wall: sign-in, "
         "and desktop worked on each", "What the owner did not try is not claimed"],
        ["Real machine, live image: “a local login closes the remote desktop”", "25 Nov 2026, one live image per desktop. GNOME (gdm): "
         "yes. XFCE (lightdm): yes, orderly close in 1.7 s. LXQt (sddm): yes, 0.7 s. KDE (plasmalogin): <b>failed with " + c("h1")
         + "</b> (REGISTRO F36: the orderly close did not end in 10 s and the forced one was refused by SELinux); with " + c("i1")
         + " it passed, and with " + c("i2") + " (wait of 5 s) too: forced at 5.04 s, everything stopped 0.56 s later, hook released at "
         "5.9 s, no SELinux denial, no core dump. After the install: no SELinux denial on any of the four",
         "KDE close by <i>abandonment</i> (the browser gone and the session left); programs that are slow to close on KDE; "
         + c("i2") + " on GNOME, XFCE and LXQt"],
        ["Browsers and clients", "Chrome and Firefox on Linux, driven by the checks; the owner's own tests from Windows, Linux and "
         "Android, by hand; an error of the client's clock found from a Windows notebook (REGISTRO F23)",
         "Safari and iOS; Firefox on Windows and on Android; IPv6"],
        ["Life cycle", "Reattach, Log Out, restart of the service, network drop, simultaneous entries, one user leaving while another works "
         "(" + c("prove/check-lifecycle.py") + ", " + c("prove/check-resilience.py") + "): part of the final round; the local-login hold ("
         + c("prove/check-prelocal.py") + ", the real login proved by hand as above)",
         "The 30-min and 60-min clocks at their real values (only the mechanism at short values). The result of " + c("check-resilience.py")
         + " on Fedora alone is not recorded in the plan"],
        ["Package", "Build with the checks of " + c("build/build-rpm.sh") + " (bench code not in the binary, " + c("ldd") + " finds "
         "nothing missing and no dynamic ngtcp2 or nghttp3); installation on the four virtual machines and the four live images",
         "The behaviour of OpenSSL 4.0 beyond “the package builds and passes the checks”; a card that is not an AMD or Intel one "
         "(NVIDIA: measured on Ubuntu 26.04 on 5–6 Oct 2026, with an earlier version of the code; not run again on Fedora 45); several graphics cards with KWin alone (REGISTRO F12, not provable on the bench)"],
        ["Left open, declared", "Nothing here is hidden: a check of " + c("prove/giro-selinux.sh") + " that hides a half-dead check on KDE "
         "(" + c("check-kde-exit") + ", case “service restart”, intermittent); a language without an encoding in AccountsService "
         "(" + c("it_IT") + "); GNOME has the same construction as KDE and no last defence; Debian and Ubuntu have the same forced-close code "
         "(still untouched); a refusal of " + c("search") + " on " + sysf("/proc/sys/dev") + "; the flag " + c("force_guard_on")
         + " after a failed local-login close", "see " + rif("Appendix C — Known issues and open points")],
    ], "«TAB» — What has been checked, and where the checking stops") + \
    p("<b>Known and not ours.</b> " + c("pkexec") + " on GNOME gets an empty " + c("SHELL") + " (the same on Ubuntu); on XFCE with a "
      "confined user the panel does not start (REGISTRO F30); an " + c("avc: denied { view }") + " of " + c("xdm_t") + " on a "
      "keyring of " + c("stratisd_t") + " follows every local sign-in on gdm, with or without REMOTIX (REGISTRO F15); and KDE's "
      "background programs (" + c("kaccess") + ", " + c("kded6") + ", " + c("plasmashell") + ") abort with a core dump when the "
      "session is closed “from outside” (REGISTRO F16).") + \
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
         "(at most 4096×2304 on the protocol); the view is the size at which the page draws it", c("CANVAS") + ", " + c("VIEW"),
         rif("The RCP/1 protocol")],
        ["<b>Attach slot</b>", "The place of a user's live connection in RCP's registry: one per user; freed when the "
         "client detaches or is silent for 30 s", c("struct slot") + " in " + c("rcp.c"), rif("The RCP/1 protocol")],
        ["<b>Farewell</b>", c("FAREWELL") + ": the message that closes an RCP session, always with a reason code and a "
         "sentence; the server never closes without saying why", c("rcp.h"), rif("The RCP/1 protocol")],
        ["<b>Sentinel</b>", "The code that asks logind whether a user has a local graphical session, and whether the "
         "remote one has no seat", c("sentinel.c"), rif("Security model")],
        ["<b>Found again</b>", "A desktop with no child whose user returns within the few seconds before the root side ends it "
         "(“no orphan desktops”); after an orderly stop there is none", c("rediscover.c"), rif("Startup and life cycle")],
        ["<b>Belts</b>", "The three settings that forbid power-off, reboot and suspend to every user: a polkit rule (active), "
         "and two sets of settings that the package ships switched off in " + sysf("/usr/share/remotix/belts/") + " (power keys and lid, sleep), left to the administrator", c("remotix-no-poweroff.rules"),
         rif("Security model")],
        ["<b>Budget</b>", "An optional admission check in megapixels per second; off by default", c("budget.c"),
         rif("Quality, degradation and budget")],
        ["<b>SELinux domains</b>", c("remotix_t") + " is the domain of the root side and " + c("remotix_net_t") + " the one of the network side, "
         "which the root side enters by writing the exec context before the " + c("execve") + "; " + c("remotix_hook_t") + " is the "
         "domain of the local-login hook. Nothing else of the product runs confined: the user's session keeps the user's own context",
         c("selinux/remotix.te") + ", " + c("walls.c"), rif("The network side and its walls")],
        ["<b>PAM hook</b>", c("remotix-pam-hook") + ": the script that puts a " + c("pam_exec") + " line into the PAM stacks of gdm, "
         "plasmalogin, lightdm and sddm, so that a local login can close the remote desktop first; it never touches what authselect "
         "generates (REGISTRO F6, F9, F21)", c("src/remotix-pam-hook"), rif("The local-login hold")],
        ["<b>KWin alone</b>", "How a KDE session gets its compositor: " + c("remotix --kwin-virtual W H -- WRAPPER ...") + " starts "
         "KWin 6.8 with " + c("--virtual"), c("kwin.c") + ", " + c("kdehost.h"), rif("The four desktops")],
        ["<b>kde_output_management_v2</b>", "The KWin protocol the child uses to set the size of the virtual screen. If KWin does not "
         "offer it (version 22 or later) the KDE session is refused", c("kwin.c") + ", " + c("child.c"), rif("Startup and life cycle")],
        ["<b>RPM Fusion, “freeworld”</b>", "The repository and the driver package (" + sysf("mesa-va-drivers-freeworld") + ") that give a Fedora "
         "machine the H.264 and HEVC encoders; the administrator installs them (PIANO D1)", c("rpm/remotix.spec"), rif("Requirements and what Fedora adds")],
        ["<b>firewalld service</b>", "The service definition " + c("remotix") + " (7447/tcp and 7447/udp) that the package installs and never "
         "opens (PIANO D5)", c("rpm/remotix.firewalld.xml"), rif("Listeners, sockets and port 7447")],
        ["<b>Runtime dconf profile, system dconf database</b>", "How the GNOME session gets its rules: a database "
         + sysf("/etc/dconf/db/remotix") + " compiled by the package (its " + c("%post") + ", or by the root side at every start if it is missing), and a profile file in the session's runtime folder that "
         "lists it. If either is missing the session runs a declared fallback", c("session.c") + " (REGISTRO C5)",
         rif("The four desktops")],
        ["<b>Session life</b>", "The three-valued answer to “is the graphical session still there?”: alive, dead (the bus "
         "answered and the name of the desktop's own service has no owner) or unknown (could not look). Only dead is certain", c("session_life()"),
         rif("Ending a graphical session")],
        ["<b>Stage refused</b>", "A stage the child declines to mount (for a screen scale other than 1, or on KDE when KWin lacks "
         + c("kde_output_management_v2") + " version 22); the message to the parent carries a <i>fatal</i> flag, the clients get 0x0E and the session is closed", c("MSG_STAGE"),
         rif("When the session ends before the stage is gone")],
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
         + c("sentinel_shutdown_forbidden()") + "); the power-off check accepts “no” and “not available on this machine” "
         "(" + c("na") + "), and an error is “not safe”. On Fedora the child's checks also include the SELinux refusals "
         "(exit codes 44 to 47, " + rif("The per-user child") + ")"],
    ], "«TAB» — The invariants quoted in the code")

S4 = p("The repository holds the product, the package recipe and the SELinux module, the build script, the checks that "
       "drive real browsers, the dev-server scripts and the specifications. Everything is in English except part of the "
       "older documents.", lead=True) + tree([
    "fedora45/",
    "├── src/            # the product: the server in C, the page, the PAM file, the polkit rules, the PAM hook",
    "│   ├── protocols/  # Wayland protocol XML files the server is built against (12 files)",
    "│   └── opus-wasm/  # the page's Opus decoder (build script and the .wasm)",
    "├── rpm/            # the package: remotix.spec, the unit, sysusers, tmpfiles, firewalld service, needrestart drop-in",
    "├── selinux/        # the SELinux module of the package: remotix.te, remotix.fc, remotix.if",
    "├── build/          # build-rpm.sh (on the build VM) and quic-static.sh (ngtcp2 and nghttp3, static)",
    "├── prove/          # the checks with real browsers: all.sh, one check-*.py per area, banco-vm/ (the VM bench)",
    "├── server/         # scripts of the dev server: the QEMU VMs with the Radeon, the live-image installer",
    "├── docs/           # SPECS.md, RCP.md, DECISIONS*.md, LESSONS.md, REGISTRO-*.md, the history of the Ubuntu work",
    "├── studio/         # the studies of the four desktops on Fedora 45 and the rules of work",
    "├── licenses/       # how-it-works.html: history of a licensing system that was dropped",
    "├── manuals/        # this manual and the user manual, generated from manuals/sources/",
    "├── LICENSE.md · THIRD-PARTY-LICENSES",
    "└── CLAUDE.md · PIANO.md   # the working rules and the plan with the current state",
], "«FIG» — The repository's folders") + \
    table(["Path", "Contents"], [
        [c("src/"), "Every " + c(".c") + "/" + c(".h") + " pair is one module; " + c("page.html") + " is the client; "
         + c("remotix.pam") + " is the PAM stack (Fedora's own stack for sshd: authselect's " + c("password-auth") + " and "
         + c("postlogin") + ", " + c("pam_selinux") + ", and " + c("pam_env") + " reading " + sysf("/etc/locale.conf") + "); "
         + c("remotix-pam-hook") + " is the script that hooks the local login into the login screens; "
         + c("remotix-no-poweroff.rules") + ", " + c("remotix-remote-sessions.rules") + " and " + c("remotix-polkit-seated")
         + " are the polkit pieces; " + c("remotix-power-keys.conf") + " is a logind belt; " + c("protocols/") + " holds 12 XML files "
         "(two of them, " + c("kde-output-device-v2") + " and " + c("kde-output-management-v2") + ", are the KDE output protocols); "
         + c("Makefile") + " builds the server."],
        [c("rpm/"), c("remotix.spec") + " (the scriptlets: " + c("%pre") + " refuses a first installation with no render node; " + c("%post")
         + " compiles the system dconf database, labels the files and applies the PAM hook; " + c("%preun") + " closes the "
         "sessions and removes the hook; " + c("%postun") + " removes the rest: an RPM has no “purge”, everything happens at removal), the unit "
         + c("remotix.service") + ", " + c("remotix.sysusers") + " (the user " + c("remotix") + "), " + c("remotix.tmpfiles") + ", "
         + c("remotix.firewalld.xml") + ", " + c("remotix.conf") + ", " + c("denied-users") + ", " + c("remotix-no-suspend.conf") + ", the KWin "
         "permission file " + c("org.kde.remotix.desktop") + " and " + c("needrestart.conf") + " (installed in "
         + sysf("/etc/needrestart/conf.d/") + ")."],
        [c("selinux/"), c("remotix.te") + " (the types and the rules), " + c("remotix.fc") + " (the file labels) and " + c("remotix.if")
         + " (the interface); the compiled module is installed by the package as " + sysf("remotix.pp.bz2") + "."],
        [c("build/"), c("build-rpm.sh") + " builds the .rpm on the virtual machine " + c("costruzione") + " (ssh port 2355 on the dev "
         "server), not in a container; " + c("quic-static.sh") + " builds ngtcp2 and nghttp3 as static libraries because Fedora's "
         "ngtcp2 (1.22.1) is older than the version needed (1.25.0) and nghttp3 1.18.0 is built with it from the same recipe, so both are linked statically ("
         + c("src/Makefile") + " lists the versions)."],
        [c("prove/"), c("prove/all.sh") + " runs, for one desktop, the base, lifecycle, multiuser, desktop, media, resilience, "
         "audio, clipboard, input, phone, prelocal and ban checks; " + c("check-package.py") + " is the Debian and Ubuntu package check (it uses dpkg): it does not apply to the RPM and is not run on Fedora (REGISTRO F29); the "
         + c("check-kde-*.py") + " checks are KDE's; " + c("prove/giro-selinux.sh") + " and " + c("wall-*") + " exercise the SELinux wall; "
         + c("giro-xfce-radeon.sh") + " and " + c("giro-lxqt-radeon.sh") + " are the rounds with the card. "
         + c("banco-vm/") + " (" + c("box.sh") + ", " + c("fresh-vm.sh") + ", " + c("autologin-lightdm.sh") + ", " + c("autologin-sddm.sh")
         + ") lets the same checks run on a QEMU virtual machine (" + c("RX_BANCO=vm") + ")."],
        [c("server/"), c("vm-radeon.sh") + " runs the virtual machines, one at a time with the graphics card handed to it; "
         + c("live-installa.sh") + " installs the package on a live image; " + c("prepara-server.sh") + " sets the dev server up."],
        [c("studio/"), "The five studies of Fedora 45 (" + c("1-gnome-fedora45.md") + ", " + c("2-kde-fedora45.md") + ", "
         + c("3-xfce-fedora45.md") + ", " + c("4-lxqt-fedora45.md") + ", " + c("5-kde-progetto.md") + "), the rules of work and the "
         "work lists of these manuals."],
        [c("docs/"), "Specifications and decisions (inherited from Ubuntu: identical files), the register of problems "
         + c("REGISTRO-problemi.md") + " (the entries F1 to F36 are Fedora's), the history " + c("STORIA-ubuntu-26.04.md")
         + " of the Ubuntu work, and the two cleaning documents: " + c("INVENTARIO-non-debian.md")
         + " (code that exists only for another distribution, still to remove) and " + c("PULIZIA-tranche1.md")
         + " (what the first cleaning removed, with proofs)."],
    ], "«TAB» — What is in the repository") + \
    note("The rules of the working copy are in " + c("CLAUDE.md") + ": Fedora 45 only, no containers, builds and tests only on the "
         "virtual machines of the dev server, and the folders of the other distributions are not to be "
         "touched. That file's “Layout” line still says that the RPM packaging is “to be written”: it is a leftover, and "
         "this manual does not rely on it.", "Working rules.")

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
    ("Package", c("rpm/") + ", " + c("selinux/"), "the spec with its scriptlets, unit, sysusers, tmpfiles, firewalld service, needrestart drop-in; the SELinux module",
     lambda f: f.startswith(("rpm/", "selinux/"))),
    ("Build", c("build/"), "the RPM build on the build VM, and the static QUIC libraries",
     lambda f: f.startswith("build/")),
    ("Checks and test rigs", c("prove/") + ", " + c("server/"),
     "the checks with real browsers, the VM bench, the dev-server scripts",
     lambda f: f.startswith(("prove/", "server/"))),
    ("Manual sources", c("manuals/sources/"), "this manual's generator, style and chapters and those of the user manual", lambda f: True),
]

S5 = p("How big REMOTIX is, part by part. The lines are counted from the sources every time the manual is generated: "
       "the files kept by git under " + c("src/") + ", " + c("rpm/") + ", " + c("selinux/") + ", " + c("build/") + ", " + c("prove/")
       + " and " + c("server/") + ", plus the manuals' own sources; binary files are left out. The last "
       "row counts every file under " + c("manuals/sources/") + ": the generator, the style, and the chapters of this manual and of the user manual.",
       lead=True) + numeri(PARTS, "«TAB» — The project's parts and their line counts") + \
    p("A large share of the C is comment: by the project's rules a non-obvious line carries the reason, the measurement "
      "or the decision behind it, often with the date. A comment is not always right: where a comment and the code "
      "disagree this manual follows the code (" + rif("Conventions") + ").")

CHAPTER = ("Introduction and concepts", [
    ("What REMOTIX is and what it promises", S1),
    ("Requirements and what Fedora adds", S1B),
    ("What was verified and what was not", S2),
    ("Basic vocabulary and the invariants", S3),
    ("The repository, folder by folder", S4),
    ("The project in numbers", S5),
])
