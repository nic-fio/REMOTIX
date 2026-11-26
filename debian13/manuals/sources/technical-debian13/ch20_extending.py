"""Chapter 20 — Extending REMOTIX and porting to another distribution. Sources: CLAUDE.md, PIANO.md,
docs/INVENTARIO-non-debian.md, docs/PULIZIA-tranche1.md, src/session.c, src/session.h, src/rcp.c, src/rcp.h, src/msgrate.h,
src/page.html, src/encoder.c, src/child.c, debian/*, prove/*."""
from build import c, h4, note, p, rif, steps, sysf, table, tip, ul, warn

# ── 20.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX 1.2.0 is written for one distribution, Debian 13 (trixie). The rule is in " + c("CLAUDE.md") + ": \"no distro detection "
       "or per-distro code (a future distro gets its own, separate code)\". The product does not read " + c("/etc/os-release") + " to "
       "choose a behaviour; where a distribution used to need a branch, the branch was removed, not generalised (" + c("docs/PULIZIA-tranche1.md")
       + "). The consequence for a maintainer is simple: a port is a separate copy of the tree with its own packaging, its own PAM file and "
       "its own test machines, not a new <code>if</code> in this one.", lead=True) + \
    p("Most of the code does not depend on the distribution at all: the transport, the RCP/1 protocol, capture, encoding, the budget, input, "
      "audio, clipboard, the page. Its dependencies are on the Linux kernel (DRM nodes, libei, PipeWire), on systemd and logind, on PAM and "
      "polkit, and on the four desktops. What depends on Debian is the thin layer listed in the next section.") + \
    note("The state of the clean-up is in two documents. " + c("docs/INVENTARIO-non-debian.md") + " lists what existed only for another distribution "
         "(or to tell distributions apart), with a verdict per item; " + c("docs/PULIZIA-tranche1.md") + " records what tranche 1 removed on "
         "17 Nov 2026, with the proof that each item was unreachable on trixie, what was left in place and why, and the risks. Line numbers in "
         "the inventory are those of the tree before tranche 1 and no longer point to the right lines.", "Where the history is.")

# ── 20.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The table lists what a porter must look at. \"Debian\" here means a fact about Debian 13 that the tree relies on. Names are files and "
       "functions, not line numbers.", lead=True) + \
    table(["Area", "What is Debian-specific", "Where"], [
        "Packaging and build",
        ["package format", ".deb through debhelper compat 13, " + c("dh-apparmor") + ", maintainer scripts calling " + c("deb-systemd-invoke") + ", "
         + c("getent") + ", " + c("systemd-sysusers") + ", " + c("systemd-tmpfiles"), c("debian/"), ],
        ["dependency names", c("libpam-systemd") + ", " + c("libpam-modules") + ", " + c("passwd") + ", " + c("dbus-user-session") + ", " + c("pipewire")
         + ", " + c("wireplumber") + ", " + c("va-driver-all") + ", " + c("mesa-vulkan-drivers") + ", " + c("labwc") + ", " + c("dconf-cli") + ", "
         + c("wlr-randr") + ", " + c("xwayland") + ", " + c("fonts-dejavu-core"), c("debian/control")],
        ["build machine", "a Debian 13 virtual machine with apt (no container); the static QUIC libraries exist because Debian's are too old", c("build/build-deb-vm.sh") + ", " + c("build/quic-static.sh") + ", " + c("server/vm-radeon.sh")],
        ["install paths", c("/usr/libexec/remotix/remotix") + ", " + c("/usr/share/polkit-1/rules.d") + ", " + c("/etc/ufw/applications.d") + ", "
         + c("/etc/apparmor.d"), c("debian/rules")],
        "Login and system integration",
        ["PAM service", "the file uses " + c("@include common-auth") + ", " + c("common-account") + ", " + c("common-session") + ", " + c("common-password")
         + ": a Debian modification of Linux-PAM; elsewhere the line is an illegal module type. It also lists " + c("pam_selinux") + " lines "
         "(module_unknown=ignore, harmless on Debian). Two " + c("pam_env") + " lines give the desktop its " + c("PATH") + " (from " + c("/etc/environment") + ") and, with " + c("/etc/default/locale") + ", the system language", c("src/remotix.pam")],
        ["language and PATH of the remote desktop", "the user's own language from AccountsService (" + c("/var/lib/AccountsService/users/<name>") + ", read as root), else the system one from " + c("/etc/default/locale") + "; the " + c("PATH") + " from PAM when it is valid, else " + c("~/.local/bin:~/bin:/usr/local/bin:/usr/bin")
         + ". Both follow what a local login gets on Debian; another distribution keeps its language settings elsewhere", c("src/child.c") + ", " + c("src/remotix.pam")],
        ["PAM service lookup and messages", "the server checks " + c("/etc/pam.d/remotix") + ", then " + c("/usr/lib/pam.d/remotix") + "; some log "
         "messages still name other distributions' file names", c("src/main.c") + ", " + c("src/authentication.c")],
        ["who is an administrator", "polkit rules name " + c("sudo") + " (Debian's polkit admin group) and also " + c("wheel") + " and " + c("admin")
         + ", which do not exist on trixie as shipped", c("src/remotix-remote-sessions.rules") + ", " + c("src/remotix-polkit-seated")],
        ["system user and directories", "sysusers and tmpfiles files; the system user " + c("remotix") + " with " + c("/usr/sbin/nologin"), c("debian/remotix.sysusers")
         + ", " + c("debian/remotix.tmpfiles")],
        ["mandatory access control", "AppArmor (profile in complain mode). SELinux code was removed", c("debian/remotix_network.apparmor")],
        ["firewall profile", "ufw application profile (defined, never opened)", c("debian/remotix.ufw")],
        ["first connection", "adds the user to the group that owns the render nodes (read from " + c("/dev/dri/renderD*") + "; not " + c("video") + ") with " + c("/usr/sbin/usermod") + "; for a user manager born before that, an ACL on the render nodes for the user's private group", c("src/child.c") + ", " + c("src/render_grant.c")],
        "Desktops",
        ["which desktop is installed", "markers " + c("xfce4-session") + ", " + c("lxqt-session") + ", " + c("startplasma-wayland") + ", " + c("gnome-session")
         + " found on the PATH; session names mapped to desktops by a substring match", c("desktop_session()") + ", " + c("desktop_of_session_name()") + " in " + c("src/session.c")],
        ["display manager readers", "the active manager from " + c("/etc/X11/default-display-manager") + " or the link " + c("/etc/systemd/system/display-manager.service")
         + "; lightdm " + c("user-session") + " and sddm " + c("[Autologin] Session") + " read from their configuration folders (valid on Debian when several "
         "desktops are installed)", c("src/session.c")],
        ["GNOME session unit", "the user unit " + sysf("org.gnome.Shell@wayland.service") + " as a real file (GNOME 48 on trixie)", c("src/session.c")],
        ["compositor for XFCE, LXQt, KDE", "Debian's labwc (0.8.3 on trixie); on KDE labwc is also used so that the desktop takes the window's size at reattach",
         c("debian/control") + ", " + c("src/wlroots.c") + ", " + c("src/kwin.c")],
        ["KWin quirks", "runtime probes for KWin 6.3 (trixie) and later; no version test in the code", c("src/kwin.c") + ", " + c("src/clipboard_kde.c")],
        "Test machinery",
        ["test machines", "four virtual machines made from the Debian 13.8.0 live images, with the display managers " + c("gdm3") + ", " + c("sddm") + " and " + c("lightdm") + "; apt and the Debian names of the packages", c("server/vm-radeon.sh") + ", " + c("prove/banco-vm/")],
        ["tests", "apt in the clean-up and in the package install; Debian's package names for the browsers on the dev server and for the tools the checks need in the machine", c("prove/banco-vm/fresh-vm.sh") + ", " + c("server/prepara-server-vm.sh") + ", " + c("prove/check-package.py")],
        ["older container files", "images with " + c("task-<de>-desktop") + ", still in the tree and not used by the VM bench", c("boxes/Containerfile") + ", " + c("boxes/set-dm.sh")],
    ], "«TAB» — Where the code depends on Debian") + \
    p("The state of each item (removed, left, or to be removed later) is in " + c("docs/INVENTARIO-non-debian.md") + ", section \"Status after tranche 1\".")

# ── 20.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The following code existed on the way from the old multi-distribution product to this tree and was removed because it cannot be reached on "
       "trixie (" + c("docs/PULIZIA-tranche1.md") + "). A porter will meet each of these problems again; the old repository, which is a read-only "
       "reference, still has the code.", lead=True) + \
    table(["Removed", "What it did", "Needed again on"], [
        ["SELinux handling in " + c("child.c") + " and " + c("walls.c"), "set the SELinux level of a login like sshd; set the exec context of the network side; the " + c("-ldl") + " link flag",
         "a distribution with SELinux enabled by default"],
        ["Ubuntu session names in " + c("desktop_of_session_name()"), "mapped " + c("xubuntu") + ", " + c("lubuntu") + ", " + c("kubuntu") + ", " + c("ubuntu"),
         "Ubuntu and its flavours"],
        ["os-release match in " + c("gnome_session()"), "chose a gnome-session whose name equals os-release ID", "a distribution with its own GNOME session name"],
        ["the GNOME 50 template branch of " + c("unit_shell()"), "handled the template unit " + sysf("org.gnome.Shell@.service"), "a distribution with GNOME 50 or later"],
        ["D-153 folder discovery (the session as a local login gives it)", "used Ubuntu's " + c("Xsession.d/60x11-common_xdg_path") + " mechanism; " + c("local_session()")
         + " now returns an empty structure and writes the same log line", "a distribution that ships that x11-common patch"],
        ["the EI-ping build switch (item 8 of the tranche-1 list), the fallback", "built without input receipts for libei older than 1.3.901", "a distribution with an older libei"],
        ["the own-labwc build switch (item 9) and the " + c("LABWC=") + " knob of the Makefile", "the patched or own labwc path", "a distribution whose labwc is too old or has a defect"],
        ["the 90-default-privs branch of " + c("remotix-polkit-seated"), "openSUSE's polkit-default-privs", "openSUSE"],
        ["1.0 to 1.5 upgrade machinery", c("remotix-net-move") + ", the non-split unit and tmpfiles", "never, unless an upgrade path from an earlier version is wanted"],
    ], "«TAB» — Branches removed in tranche 1") + \
    h4("What stays and why") + \
    ul([
        "The " + c("/usr/lib/pam.d") + " lookup and the other distributions' texts in the PAM messages: " + c("/usr/lib/pam.d") + " is a real PAM vendor "
        "directory on trixie, so the lookup is not provably dead. Only text.",
        "The " + c("pam_selinux") + " lines of " + c("remotix.pam") + ": the module ships with Debian's libpam-modules and the lines mirror Debian's sshd.",
        "The lightdm and sddm readers and " + c("declared_desktop()") + ": valid on Debian when several desktops are installed.",
        "The KWin 6.5 and 6.6.6 workarounds: runtime probes, not version tests.",
        c("wheel") + " and " + c("admin") + " in the polkit rule: logic, kept.",
        "The " + c("--no-split") + " run-time option and " + c("TWIN") + " and " + c("fingerprints") + " in the Makefile.",
        "Several header comments that mention other distributions, and the " + c("Ubuntu") + " name in the page's font stack.",
    ]) + \
    h4("Risks recorded by tranche 1") + \
    ul([
        "The session-folder lookup that imitated a local login (D-153) relies on x11-common not shipping " + c("60x11-common_xdg_path") + ". If a future Debian adds it, the removed "
        "code (never tested on Debian) would be needed again.",
        "An administrator who installs SELinux on Debian finds no SELinux handling in REMOTIX.",
        "A build against libei older than 1.3.901 now fails at " + c("make deps") + " by design.",
        "On " + c("apt remove") + " (not purge) the certificates and ban list now stay in " + c("net/") + " instead of moving back to the 1.0 location; "
        "a check that looks for the 1.0 location will not find them.",
    ]) + \
    p("Still to do (tranche 2, listed under \"needs care\" in the inventory): the remaining Ubuntu and Xubuntu detection in " + c("session.c") + ", "
      "the Ubuntu emulation of a local login's " + c("XDG_*") + " variables, comments naming other distributions, and cosmetic items. The list "
      "also appears in " + rif("Appendix C — Known issues and open points") + ".")

# ── 20.4 ─────────────────────────────────────────────────────────────────────
S4 = p("The tree is not a template for a port, but the porting questions are known. The list below is derived from the inventory and from the "
       "table above; it has not been exercised, because no second distribution exists yet.", lead=True) + \
    steps([
        "<b>Start from a copy,</b> not from a branch of this tree: " + c("CLAUDE.md") + " says the future distribution gets its own, separate code.",
        "<b>Check the library minimums</b> in " + c("src/Makefile") + " (" + c("MINIMI") + "): OpenSSL 3.5 or newer, GLib 2.80, libei 1.3.901, "
        "PipeWire, libva, Vulkan loader 1.3.274. The QUIC libraries are built from source in the image whatever the distribution carries.",
        "<b>Rewrite the package</b> for the new format: dependency names, install paths, maintainer scripts. Keep the guards of " + c("debian/rules")
        + " (R13, R24) and the checks of " + c("build/build-deb.sh") + " (R4, R13, R14, R23) as requirements, however they are implemented.",
        "<b>Write the PAM service file</b> for that distribution's stack. Without the file, Linux-PAM falls back to the service " + c("other") + ", and what "
        + c("other") + " does depends on the distribution (on some it is a hard deny, so every right password is refused). The program checks "
        "the file at start-up (" + c("main.c") + ").",
        "<b>Check polkit and administrator groups:</b> the rules directory, the group that polkit calls administrator, and whether a default privilege "
        "table overrides the rules.",
        "<b>Check the display manager and session names</b> the desktops register, against " + c("desktop_session()") + " and the readers in " + c("session.c")
        + ".",
        "<b>Check mandatory access control.</b> If SELinux is on, the removed handling of " + c("child.c") + " and " + c("walls.c") + " is needed; "
        "for AppArmor, adapt the profile (it is shipped in complain mode; " + c("check-apparmor.py") + " reads the kernel journal of every round and fails on any line of the profile, so adapt it until a round shows none).",
        "<b>Check the compositor,</b> labwc, at the version the distribution carries, and the four desktops' versions, in particular the GNOME "
        "session unit shape and the KWin quirks.",
        "<b>Make the test machines:</b> one virtual machine per desktop really installed from the distribution's live image (" + c("vm-radeon.sh crea") + " is the Debian model), the ports "
        "and names in " + c("banco-vm/box.sh") + " and " + c("lib.py") + ", and run the whole of " + c("prove/all.sh") + " on each desktop (" + rif("Testing") + "). On a new distribution or desktop also try by hand, on a real machine started from a live USB stick, "
        "the local login with programs open in the remote desktop (" + rif("Testing the real machine from a live USB") + ").",
        "<b>Run the package check</b> (" + c("check-package.py") + "): install, first start, remove, purge, reinstall.",
    ]) + \
    warn("Do not add a branch for the new distribution to this tree. If code is shared, move it first; the two trees must not need each other.")

# ── 20.5 ─────────────────────────────────────────────────────────────────────
S5 = p("RCP/1 is closed by design: a receiver that does not understand a message must close with the reason " + c("RCP_PROTOCOL_ERROR") + " (0x0B), and a "
       "capability used without having been negotiated is the same error (" + rif("The RCP/1 protocol") + "). So adding a message is a protocol change, "
       "with the page and the server changed together. The places to touch, in order:", lead=True) + \
    steps([
        "<b>Specify it first</b> in " + c("docs/RCP.md") + " (the message list of §7, the byte layout of §6, the version rules of §9) and in "
        + c("docs/SPECS.md") + " if it adds a promise. Decide whether it needs a capability in " + c("HELLO") + " and " + c("HERE_I_AM") + ".",
        "<b>The type number</b> in the right enumeration of " + c("src/rcp.c") + ": the control channel (low byte, e.g. " + c("T_TERMINATE_SESSION = 0x0011") + "), "
        "input (high byte 0x01), clipboard (0x02), video (0x03) or the audio datagram (0x0401). The same constant goes into the " + c("TYPE") + " table of "
        + c("src/page.html") + ".",
        "<b>The body length check.</b> " + c("measure_fields()") + " in " + c("rcp.c") + " reads the fields of a body before the message is acted on. A type missing "
        "from it falls into the default and the check after the switch sends the client away after the action (the comment above " + c("measure_fields()")
        + " records what that order cost with " + c("HELLO") + ", " + c("ATTACH") + " and " + c("CREDENTIALS") + "). For a fixed-size input message also update the lengths in the comment block of the input enum.",
        "<b>The handler</b> in the dispatch switch of the channel (the control handler holds " + c("case T_HELLO") + " to " + c("case T_TERMINATE_SESSION") + "). "
        "If it needs the host (the transport or a session), add a hook to the struct of function pointers in " + c("src/rcp.h") + ", with its comment, "
        "and connect it in " + c("webtransport.c") + " or " + c("main.c") + ".",
        "<b>The rate class.</b> Messages that a client can send in a flood have a class in " + c("src/msgrate.h") + " (" + c("MC_POINTER") + " ... " + c("MC_FIT_CANVAS")
        + ", with a rate and a burst) and a mapping in " + c("control_class()") + " or " + c("lww_index()") + " in " + c("rcp.c") + ". A new message needs a "
        "decision: its own class, or one that is never dropped.",
        "<b>The page,</b> both directions: how it encodes or decodes the message, and what it does on an unexpected type. A server message the page does not know "
        "ends the session with " + c("PROTOCOL_ERROR") + ".",
        "<b>Log lines</b> follow " + rif("Conventions") + " (the mark at the head of a body sets the journal priority).",
        "<b>A check:</b> a new name in an existing check, or a new check file (below). The test is the page driven by a real browser, so the page and the server "
        "are tested together.",
    ]) + \
    note("There is no unit-test harness for " + c("rcp.c") + " in this tree: the twin comparison and the benches that exercised the protocol alone were not carried "
         "over (" + rif("Build and release") + "). A protocol change is covered only by what the checks of " + c("prove/") + " exercise.", "No protocol-level tests.")

# ── 20.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The product knows four desktops, by the enumeration " + c("DesktopSession") + " in " + c("src/session.h") + ". A fifth is a larger change than it looks, "
       "because the desktop appears in places beyond " + c("session.c") + ". The order that the code and its comments suggest:", lead=True) + \
    steps([
        "<b>Classify the family.</b> Capture, input, clipboard and remount talk to the compositor, not the desktop. XFCE and LXQt share labwc, a "
        "wlroots compositor, and " + c("session_on_wlroots()") + " answers \"is it the wlroots family\"; GNOME uses Mutter and KDE uses KWin. A new desktop that "
        "runs on labwc reuses the whole wlroots path.",
        "<b>The enumeration.</b> Add the value to " + c("DesktopSession") + " at the END: the value travels as a " + c("uint32_t") + " between the parent and the "
        "child, and renumbering the existing ones would break that boundary.",
        "<b>Detection.</b> " + c("desktop_session()") + " in " + c("session.c") + " chooses by markers on the PATH, in a stated order (the comment lists the six branches "
        "and why the order is not free), and " + c("desktop_of_session_name()") + " maps session names. Add the marker and the name, and decide what happens "
        "when two desktops are installed (the code picks one and says so in the log).",
        "<b>The names of the desktop's session</b> as macros in " + c("session.h") + " (for XFCE, " + c("SESSION_PRIMARY_XFCE") + " and " + c("SESSION_BUS_XFCE")
        + "), and its Log Out command.",
        "<b>The places that branch on the desktop.</b> In " + c("child.c") + ", the birth of the session and the stage (the XFCE and LXQt wording and the KDE "
        "branch), and the close; in " + c("main.c") + ", the switch that names the desktop in the log; in " + c("session.c") + ", the branches that are specific to one desktop "
        "(for example the GNOME-only ones). Search for " + c("SESSION_DESKTOP_") + " to find all of them.",
        "<b>Packaging.</b> Recommends in " + c("debian/control") + " if the desktop needs a compositor package, and a test machine: add the desktop to "
        + c("banco-vm/box.sh") + " (the " + c("choose") + " function: ports and names), " + c("lib.py") + " (" + c("PORTS") + ") and " + c("vm-radeon.sh") + ".",
        "<b>Tests.</b> Add the desktop to the dictionaries of the checks: " + c("PANEL") + " and " + c("LOGOUT") + " in " + c("deskkit.py") + ", " + c("PORTS")
        + " and " + c("SHELL_UP") + " in " + c("lib.py") + ", " + c("TERMINAL") + " and " + c("FILEMGR") + " in " + c("check-desktop.py") + ", the desktop list in "
        + c("all.sh") + " and " + c("matrix.sh") + " (" + c("fresh.sh") + " takes the desktop as its argument). Then run the full suite on it.",
    ]) + \
    p("The four existing desktops are described in " + rif("The four desktops") + ". The comments in " + c("session.h") + " record what each addition cost: for "
      "example that, before LXQt, five places wrote the XFCE test directly, so the fifth value would have fallen into the GNOME and KDE branch silently.")

# ── 20.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The chain is: card capability, encoder route, codec number in RCP, the offer in " + c("HERE_I_AM") + ", the page's decoder. Video encoding is described "
       "in " + rif("Video encoding") + "; for an addition:", lead=True) + \
    steps([
        "<b>Encoder.</b> Routes are chosen by capability when each encoder opens (" + c("h264_card") + " and " + c("hevc_card") + " in " + c("src/encoder.c") + ": "
        "Vulkan first, VA-API where Vulkan is not there). A codec needs an implementation on each route that can carry it (" + c("vadirect.c") + " for VA-API, "
        + c("vulkanvideo.c") + " for Vulkan) and an entry in the capability probe.",
        "<b>The measurement at start-up.</b> " + c("child_video_capabilities()") + " measures what the card encodes and the result becomes the offer: "
        + c("rcp_video_codec_set()") + ". With an empty list every " + c("HELLO") + " ends in " + c("RCP_NOTHING_IN_COMMON") + ".",
        "<b>The number in RCP.</b> Codec numbers are never reused: 1 is HEVC, 2 stays AV1 even though AV1 left the product, 3 is H.264 (the comment in "
        + c("page.html") + " gives the reason: an old client hearing a reused number would paint garbage without an error). " + c("RCP_CODEC_VIDEO_MAX")
        + " in " + c("rcp.h") + " bounds the list.",
        "<b>The page.</b> The tables " + c("CODEC_RCP") + " and " + c("CODEC_NAME") + ", the preference list " + c("PREFERENCE") + ", and the capability "
        "probe (the page asks the browser whether it can decode the codec string) in " + c("src/page.html") + ". The server decides in the end; the page's "
        "list is a preference.",
        "<b>The keyframe rules</b> of RCP §5.2 apply to every codec: the first frame after " + c("SESSION") + ", after a canvas change, and on request.",
        "<b>Tests.</b> The " + c("codec") + " check of " + c("check-media.py") + " reports the negotiated codec per browser and that it is hardware; a new codec "
        "needs its own expectation there and in the sharpness judge.",
    ]) + \
    note("HEVC is offered by the server but did not reach the pixel on the browsers of the test machine in the final round of 17 Nov 2026 (the page's probe "
         "refused every HEVC string, on Chrome and on Firefox, on the four desktops); every recorded run negotiated H.264 (server logs " + c("prove/log/v160-<de>/media.out")
         + ", check " + c("codec") + "). HEVC decoding in a browser is therefore not demonstrated by the logs.", "State of HEVC.")

# ── 20.8 ─────────────────────────────────────────────────────────────────────
S8 = p("A check is cheap to write and expensive to trust. The conventions below are what the existing checks do (twelve " + c("check-*.py") + " files; " + c("all.sh") + " runs eleven of them, " + c("check-package.py") + " is run apart); a new check should do the same.", lead=True) + \
    steps([
        "<b>One file, one docstring.</b> Put the check in " + c("prove/check-<name>.py") + ". The docstring says what it proves, how to run it, the users it makes, "
        "and the verdict names. Define a " + c("NAMES") + " tuple.",
        "<b>Use the kit.</b> Build on " + c("lib.py") + ": " + c("Results") + " for verdict lines (" + c("attempt") + " turns an exception into FAIL or BLOCKED; "
        + c("sequence") + " runs the checks in order under a deadline), " + c("Rig") + " for compositor, browser, user and login, " + c("deskkit.py") + " to run things in the user's session.",
        "<b>FAIL is the product, BLOCKED is the tool.</b> Raise " + c("Fail") + " when the product did not do it; let a tool error surface as " + c("ToolError") + ".",
        "<b>Use a user prefix of its own</b> and add it to the pattern of " + c("lib.sweep()") + " so that sessions are ended at the end of " + c("all.sh") + ".",
        "<b>Judge from inside the box.</b> Log what the application received (a test window), not what the browser was told to send. If a new window is "
        "needed, add it next to " + c("window.py") + ".",
        "<b>Print evidence on the line.</b> The format is " + c("PASS|FAIL|BLOCKED <name> - evidence") + ", one line per name.",
        "<b>Register it in all.sh</b> with a time limit: " + c("run <label> <seconds> python3 check-<name>.py --box \"$DE\"") + ". A check that changes the box in "
        "a way that other checks must not see (like " + c("check-ban.py") + " and " + c("check-package.py") + ") goes last or outside.",
        "<b>Prove that it can say red.</b> A check that cannot fail is a net with no fish. The existing checks keep a " + c("--selftest") + " for the picture judge "
        "(" + c("base-check.py") + ") and report numbers in their evidence so that a pass can be read.",
        "<b>Record a limit honestly.</b> If the check is an emulation (the phone) or has a declared tool limit (AltGr), write it in the docstring.",
    ]) + \
    p("Running order and limits are in " + rif("Testing") + ".")

CHAPTER = ("Extending REMOTIX and porting to another distribution", [
    ("The one-distribution rule", S1),
    ("Where the code is Debian-specific", S2),
    ("What the clean-up removed, kept and risked", S3),
    ("A checklist for porting to another distribution", S4),
    ("Adding a message to RCP/1", S5),
    ("Adding a desktop", S6),
    ("Adding a video codec", S7),
    ("Adding a check to prove/", S8),
])
