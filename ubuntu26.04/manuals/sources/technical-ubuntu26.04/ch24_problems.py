from build import c, note, p, rif, sysf, table, ul, warn

def items(rows, cap):
    return table(["Item", "State"], rows, cap)

S_INTRO = p("This appendix lists what is known to be open, unverified or inconsistent in REMOTIX 1.0.0 for Ubuntu 26.04, area by area. It is "
            "meant to be complete rather than flattering. An item is here because a source file, a check, the problem register "
            "(<code>docs/REGISTRO-problemi.md</code>) or <code>docs/STORIA-ubuntu-26.04.md</code> (the history of the work) says so; where something was read only in a comment and not observed, it is said. "
            "Two sections are specific to this tree: what real machines showed that the container boxes did not, and the open points of the Ubuntu port. "
            "The last section lists the places where code, comments and documents disagree: in every case the code "
            "was taken as the truth and the chapters describe the code.", lead=True) + \
    note("The package <code>remotix_1.0.0-1+ubuntu26.04_amd64.deb</code> (the test build named <code>unione10</code>) had one full round of <code>prove/all.sh</code>, on the GNOME virtual machine, on 19 Nov 2026: "
         "120 lines PASS, 2 FAIL, 1 BLOCKED, 3 SKIP (see the chapter on testing). The FAIL <code>desktop/users-shell-and-environment</code> is a known limit below; the FAIL <code>ban/typed-names-not-logged</code> was "
         "a false red of the bench (the lines found were written by <code>sudo</code> for the check's own command) and the BLOCKED Firefox audio check was the test browser failing to answer on its first start; "
         "after the bench began to enter the machine as root, the ban checks and the Firefox audio check were run again and passed. The full round was not repeated after that change. "
         "The other three desktops had a short start-up check with the passed-through graphics card and the owner's hand tests. The full round is of the test package <code>unione10</code>, whose polkit rule has 15 actions, while this manual describes the rule with 19 (package <code>unione11</code>): the build checks are the same, but there is no full round of it, only the partial one of the polkit entry below. Nothing in this appendix is a failure of the round "
         "unless it is stated so.", "Scope.")

S_UNVERIFIED = items([
    ["AppArmor in a session", "The profile <code>remotix_network</code> is in complain mode. On Ubuntu 26.04 it was observed in real sessions: the log line <code>§5.1 … CONNECTED</code> was read on the live images of Ubuntu and Kubuntu and on the four virtual machines (register C4); for the Xubuntu and Lubuntu live images only the owner's report of a successful sign-in exists. <b>Enforce mode was not tried.</b> "
     "The known limit of the profile (an abstract socket that binds itself a name) is below. The profile judges the resolved path, which is why the XKB data of xkb-data 2.46 are listed under their real folder."],
    ["A real phone", "Touch behaviour is proven only by emulation in <code>prove/check-phone.py</code>. On Ubuntu the owner used an Android phone (Chrome) and a tablet on the virtual machines: Kubuntu was \"regular\" on both, and "
     "Ubuntu GNOME showed small stutters in the video on the phone (" + rif("Ubuntu: open points") + ", E4); detach and reattach from Linux and from Android, at different sizes, "
     "were fine on all four machines. A Samsung DeX was tried on GNOME in the container boxes on 19 Nov 2026 (OK); it was <b>not repeated on the virtual machines nor on the other three desktops</b>. On the virtual machines the owner tried Linux and Android clients on all four desktops on the evening of 19 Nov. Safari, iOS and a Firefox on Windows were never tested."],
    ["GNOME, first tap after login", "The first touch tap can land on the initial point if the pointer position arrives before "
     "Mutter is ready (<code>touch_announce_pointer</code>). Seen on Debian 13 (1 case in 13); not proven; low priority. Not re-measured on Mutter 50 (not verified on Ubuntu 26.04)."],
    ["NVIDIA", "No NVIDIA card was used with this tree. Comments cite measurements on a rented RTX 4090 of an earlier build; "
     "the group of <code>/dev/nvidia*</code> is not handled by the grants. The Intel integrated card with GNOME 50 was also never run with the functional suite."],
    ["4096×2304", "The coded limit is 4096×2304; the declared limit is 3K. In the Ubuntu round <code>canvas-limits</code> passes on GNOME, and a view of 4096×2304 or 5120×2880 gives a canvas of 3840×2160, "
     "the last rung of the page's own size ladder. Nothing larger was obtained, and no frame rate or quality figure exists at those sizes."],
    ["Capacity", "At most three users were attached together in the checks (GNOME), and no run was made at the default cap of 10 sessions, nor at "
     "the declared limit of 8 users. No capacity figure exists for this tree."],
    ["Reproducible build", "The build checks of the test package <code>unione10</code> (file <code>controlli.txt</code> on the dev server) say that two clean copies gave the identical package "
     "(<code>R23 riproducibile SI</code>), that the source archive of our labwc is identical in two builds, that <code>ldd</code> finds no missing library and no <code>libwlroots</code> in our labwc, and "
     "that the bench is not compiled into the binary (<code>R13</code>); <code>lintian</code> reported one informational tag (the unit has no documentation key). QUIC library tags are pinned by version, not by hash."],
    ["Local-session refusals", "Ubuntu and Kubuntu were tried by the owner on the real login screens of live images (GDM and SDDM): the local login was held, the remote desktop was closed and the local login went on "
     "(" + rif("Ubuntu: what real machines showed that the boxes did not") + "). For <b>Xubuntu and Lubuntu</b> (LightDM, SDDM) the hold was <b>not tried</b> on a real login screen: "
     "the live images were used only to sign in remotely. <code>prove/check-prelocal.py</code> simulates the local login by calling the hook (six steps, all PASS in the round); the real-greeter line is a declared SKIP. "
     "No automatic check covers reason 0x05."],
    ["Network hardening", "No check floods the server, rotates the page certificate, sends malformed RCP bytes, or uses IPv6. "
     "The packaged unit binds IPv4 only."],
    ["Versions of XFCE and LXQt on Ubuntu 26.04", "Read in the container boxes (studies 7 and 13, the first rounds): xfce4-session 4.20.4, xfce4-panel 4.20.7, libxfce4windowing 4.20.5, lxqt-session 2.3.0, lxqt-panel 2.3.2, labwc 0.9.3. "
     "Comments in the source still cite 2.1.x and labwc 0.8.3 (listed with the contradictions). The versions on the installed flavour images were not re-read."],
    ["Settings model, branches tried only by reading", "Register C5 lists two branches of the dconf correction as not tried in the field: the \"life unknown\" answer at the start of a child (in the new model and in the fallback), and the "
     "\"database different or older\" case of the compilation at service start (only \"database missing\" was tried). The reviewers approved the package by reading the code. The sources read do not show a run of "
     "the fallback with <code>dconf</code> absent, nor of an administrator's <code>DCONF_PROFILE</code> in the environment of the child itself (the case tried was one set only in the user manager's environment, <code>environment.d</code>): "
     "both are <b>not verified on Ubuntu 26.04</b>."],
    ["Measured figures in comments", "Figures such as the pixel scan time, the 160 ms drift, the 1.86/0.97 Gpixel/s conversion rates and the "
     "39.54 fps drawn by GNOME at 60 Hz come from comments of earlier builds and were not re-measured on Ubuntu 26.04. The figures that comments of this tree carry (KWin 6.6.7, Mutter 50) are dated 18 and 19 Nov 2026 and name their machine."],
    ["Package check", "<code>prove/check-package.py</code> (install, first start, remove, purge, reinstall) was never run on Ubuntu 26.04 and is not part of the virtual-machine bench: it is a declared SKIP. "
     "No real removal or purge was ever done on Ubuntu. The installs on the virtual machines exercise the <code>postinst</code> (and the upgrade runs of <code>prerm</code> and <code>postrm</code> with <code>--reinstall</code>); the purge block was run once, alone, extracted into a script, on one virtual machine (the user's file removed, the user's settings intact: \"simulated purge\" in the history)."],
], "«TAB» — What was not verified.")

S_LIMITS = items([
    ["Declared limits of the product", "Resolution up to <b>3K</b> (the size actually used depends on the client) and <b>8 users</b> at the same "
     "time. Owner's decision, <code>DECISIONS-11</code> §11.51, confirmed 18 Nov 2026. The program technically accepts more (a protocol "
     "canvas of 4096×2304, a probe ladder in the page up to 3840×2160, <code>--session-cap</code> default 10), but those are not the declared values."],
    ["XFCE: black background in the remote desktop", "<b>Seen on Debian 13, not seen on Xubuntu 26.04.</b> On Debian the wallpaper of the remote desktop was black (register E1): <code>libxfce4windowing</code> 4.20.2 loses the "
     "compositor's message that says on which screen the work area is, when it arrives before the screen is known; it was corrected by its authors from 4.20.4. Xubuntu 26.04 was seen with a normal wallpaper on 18 Nov 2026 "
     "(container round, library version 4.20.5) and on 19 Nov 2026 (control picture of the Xubuntu virtual machine). The version on the installed Xubuntu image was not read. XFCE keeps one wallpaper per screen: the one chosen locally does not "
     "pass to the remote screen by itself."],
    ["Service killed and not yet restarted", "If the service is killed outright (SIGKILL, a crash) there is a window of about 2 s, until systemd restarts "
     "it, in which nobody can close the desktop left behind. The restarted root side then ends it unless its user returns first (“no orphan desktops”; "
     + rif("Desktops found again after a restart") + ")."],
    ["How the local-login hold was proven", "By the owner, on real login screens of live images of Ubuntu 26.04.1: <b>GNOME</b> (GDM): the local login was held in PAM, the remote desktop was closed in 851 ms, the client "
     "got 0x04, the runtime dconf profile was removed in the same second, the local login went on, and after a local Log Out a new remote login worked. <b>KDE</b> (SDDM, Kubuntu): held in PAM, client sent away "
     "with 0x04, desktop closed by its child in <b>10.9 s</b> (on GNOME 0.85 s: the closing time of KDE, section D of the register), then the local login went on; nothing in <code>/var/crash</code> on either. <b>XFCE and LXQt:</b> not tried on a real login screen. "
     "In the automatic checks the local login is <b>simulated</b> by calling the hook by hand (<code>check-prelocal.py</code>): the virtual machines have a real login screen, but it cannot be driven by a check. "
     "On Debian 13 (not repeated here) the same hold was shown on GNOME on the tablet and, as reported by the owner, on KDE, XFCE and LXQt live systems."],
    ["GNOME, graphical password window (<code>pkexec</code>)", "The automated check (<code>desktop/users-shell-and-environment</code>) fails on Ubuntu: it is the only check line of the GNOME round that is a FAIL for the product's sake. <code>SHELL</code> is empty in every GNOME remote session, "
     "by design of the composed environment (<code>session.c</code>), and <code>pkexec</code> then refuses to start (\"the value for the SHELL variable was not found in the /etc/shells file\"), so polkit's agent is asked zero times and no password window appears. "
     "<code>sudo</code> (sudo-rs on Ubuntu 26.04) answers as usual. Whether the password window appears on a real machine was not verified; if it does not, use <code>sudo</code> in the terminal (<code>ptyxis</code> on GNOME)."],
    ["Kernel with mediation of unix sockets", "On Ubuntu 26.04 (kernel 7.0) AppArmor mediates unix sockets, which the container bench and the Debian kernel did not show. The profile now names its operations (register C4; "
     "" + rif("Ubuntu: what real machines showed that the boxes did not") + "). The one known limit, the abstract socket that binds itself a name, is in " + rif("Ubuntu: open points") + "."],
    ["Programs with their own settings reader", "Snap programs and Flutter programs of Ubuntu do not read the session's settings through the environment variable the first model used. The system database <code>/etc/dconf/db/remotix</code>, "
     "the runtime profile and the user database <code>~/.config/dconf/remotix</code> replaced it (register C5). One small file of ours stays in the user's home until <code>apt purge</code>."],
    ["Scale of the user", "A user whose own settings ask for a scale other than 1 would see a distorted layout and a pointer in the wrong place. On GNOME the child brings its monitor to scale 1 once, temporarily, with at most three D-Bus calls of 15 s each (about 45 s in a broken Mutter); "
     "if that does not work it refuses the stage, the clients get 0x0E and the session is closed (a <code>fatal</code> flag of the stage message)."],
    ["RealtimeKit in the containers (history)", "In the container boxes RealtimeKit does not start and holds the exit of a young child for 25 s (register B2); the check had to wait for 31 s on Debian 13. It is an artefact of the container bench. "
     "The code still allows up to 25 s for a process to leave where the service is installed and does not answer, which is why the child now tells the clients first. On the virtual machines it was not measured."],
], "«TAB» — Known limits of this release.")

S_REAL = p("Four problems were found only when the product ran on a real or virtual system, with a real login screen, the security module in force and the confined programs of Ubuntu. "
           "The container boxes had none of these. One more entry, on the polkit rule, closed on 20 Nov 2026. The register entries are cited by their letter.", lead=True) + \
    items([
        ["<b>Closed.</b> C4: every sign-in refused (19 Nov 2026)", "The first sign-in on a real Ubuntu 26.04.1 image (kernel 7.0) was refused for every user: \"the server could not open your session\", and the journal said <code>logind unreachable (Unable to create socket: Permission denied)</code>. "
         "The network side's profile had <code>deny unix addr=@*</code>, which also carries the permission to create a socket (it has no address): on a kernel that mediates unix sockets it forbade every socket, so no D-Bus and no question to logind; "
         "REMOTIX, unable to prove that no local session exists, refuses. A <code>deny</code> holds in complain mode too and leaves no warning line. The fix is two lines that name their operations (<code>deny unix (bind, listen) addr=@**,</code> and "
         "<code>deny unix (connect, send, receive) peer=(addr=@**),</code>; two stars because one stops at the slash). Measured on the machine afterwards: the system bus and the journal reachable, abstract sockets still refused, the local-session check \"CONNECTED\". "
         "The residual limit is in " + rif("Ubuntu: open points") + "."],
        ["<b>Closed.</b> C5: snap and Flutter programs did not digest the session's settings profile (19 Nov 2026)", "The installer of the live image showed \"Something went wrong\" (<code>Unknown DConf source</code>); Firmware Updater and Security Center said <code>No DConf source to write to</code>. "
         "The first model passed the rules with <code>DCONF_PROFILE</code> pointing to a three-layer profile in a run folder; the Flutter programs have their own dconf reader that knows only <code>user-db</code> and <code>system-db</code> and drops the whole profile at any other line, and the confined snaps have another "
         "<code>XDG_RUNTIME_DIR</code> and cannot open the path. The fix: the blocks became the system database <code>/etc/dconf/db/remotix</code>, built by the package from the table <code>DCONF_KEYS</code> of <code>session.c</code> (<code>remotix --dconf-keyfiles</code>); the session no longer has <code>DCONF_PROFILE</code> "
         "and writes <code>$XDG_RUNTIME_DIR/dconf/profile</code>; the values that change while the session lives go in the user database <code>~/.config/dconf/remotix</code>. The service compiles the database at start if it is missing or different. A profile that is not ours is never overwritten: the declared fallback "
         "(three layers compiled on the fly, <code>DCONF_PROFILE</code> with the path) is used and the log says <code>DECLARED FALLBACK, D-015 (19 Nov 2026)</code>. Confirmed on a real live image on 19 Nov 2026: no dconf error in the journal, and the installer starts in the remote session."],
        ["<b>Closed.</b> B3-bis: a red row, the same everywhere, was the tool (18 Nov 2026)", "Three input rows (<code>mouse-drag</code> with Chrome and Firefox, <code>tap-and-half-drag-select</code>) failed identically on the four machines, while green on Debian 13. The text was selected but the test window did not register the release. "
         "Under GTK 4.22 a text field that claims the drag denies the sequence to the gestures of its containing window; GTK 4.18 does not. The window now reads the release from raw events, and the check still fails if the release really does not arrive."],
        ["<b>Closed.</b> D: KDE, a Log Out asked in the first seconds was lost (18 Nov 2026)", "On Kubuntu 26.04 (Plasma 6.6) \"Log Out\" starts <code>plasma-shutdown</code>, which asks systemd to stop the graphical session; if a service (usually the portal) is still starting, systemd refuses, <code>plasma-shutdown</code> does not repeat and exits, and the desktop stays alive without telling the client. "
         "The old rescue waited for a unit to stop, which never happens on Plasma 6.6. Now REMOTIX notices that <code>plasma-shutdown</code> has ended, asks ksmserver whether it is really closing and, only if so, repeats the stop after 4 s (ten times \"fail\", then ten times \"replace\"); if it stays refused for about a minute it closes the session by the road the product already has. "
         "The first remedy, never released, closed the session as soon as <code>plasma-shutdown</code> started and could lose unsaved work: a Log Out must be tried with unsaved work (save, discard, cancel). Limits: a shutdown or reboot asked from the desktop does not release the name and, refused in the first seconds, would be lost (the menu entries are removed by REMOTIX); a restart of KWin during the wait resets the request."],
        ["<b>Closed.</b> C6: \"nobody can power the machine off\" was not true for the local user's reboot (20 Nov 2026)", "The owner, on his own machine, asked why it seemed possible to power off. The rule forbade 15 actions of logind and the check watched the remote session only. A local user, sitting at the machine, got \"yes\" to a reboot: "
         "four actions that were not forbidden (<code>set-reboot-parameter</code>, <code>set-reboot-to-firmware-setup</code>, <code>-to-boot-loader-menu</code>, <code>-to-boot-loader-entry</code>) carry the annotation <code>org.freedesktop.policykit.imply</code> = <code>reboot</code> and the default \"yes\" for the seated user, "
         "and polkit grants an implied action despite an explicit NO on the implying one. The rule now forbids <b>19</b> actions, and the check <code>power-implied</code> of <code>prove/check-desktop.py</code> reads the installed rule and every <code>*.policy</code> file of the machine, builds the implications (also chained) and fails if an action left alone implies a forbidden one. "
         "With other users logged in, logind asks for <code>reboot-multiple-sessions</code>, which was and is denied: the hole concerned only the lone local user. The login-screen case (the greeter user is active and local) was deduced, not measured at the time; the check <code>power-local-seat</code> measures it. "
         "<b>Evidence on Ubuntu.</b> Before the correction, the check run on the GNOME virtual machine (log folder <code>vm-gnome-poweroff-prima2</code>) said \"polkit GRANTS: reboot\" from the place of the login screen's user. With the 19-action rule, the log <code>vm-gnome-poweroff-dopo/desktop.out</code> has <code>PASS power-implied</code> (19 forbidden actions, 51 policy files read, no action left alone implies a forbidden one) and <code>PASS power-local-seat</code> (from the active session of seat0 all 19 are refused; calibration: chvt granted). The limit: it is a PARTIAL round, the desktop check alone on the GNOME machine (8 PASS and the known <code>users-shell-and-environment</code> FAIL). Closed for Ubuntu. The defect was found on a Debian 13 machine: there the same correction was made on 20 Nov 2026 (rule with 19 actions on <code>main</code>; the rebuilt package is not yet published), and the proof from the local user's place was done on 20 Nov 2026 on the owner's Debian 13 tablet with the rebuilt package: from a process of the local user's active session polkit refuses reboot, power-off, halt, suspend and the four set-reboot actions (calibration: chvt granted), and logind answers \"no\" to CanReboot and CanPowerOff; the login-screen case was not tried on Debian. "
         "On a new distribution run <code>power-implied</code> with its systemd version and try <code>pkcheck --action-id org.freedesktop.login1.reboot</code> by hand from the local session."],
    ], "«TAB» — Ubuntu: what real machines showed that the boxes did not")

S_OPEN = items([
    ["No unblock for the administrator", "By the owner's decision (17 Nov 2026) a ban ends only by itself. The command socket "
     "(<code>command.c</code>, <code>--command-socket</code>) is compiled in and used by <code>check-ban.py</code>; the packaged unit never passes it."],
    ["No firewall rule opened", "The package ships a ufw application profile; an administrator must run <code>ufw allow REMOTIX</code>. On Ubuntu 26.04 ufw is installed but disabled by default (<code>ENABLED=no</code>, studio 5), so nothing blocks the port until it is enabled."],
    ["Page certificate name", "<code>certificates_prepare()</code> does not compare an existing certificate's name with <code>--name</code>: "
     "a renamed host keeps a certificate with the wrong name until it expires."],
    ["Root-side login pauses", "Lost when the root side restarts; the global AUTH rate (3 per second, burst 8) means a ninth simultaneous login is not checked: it gets «could not check» (0x0E, not counted towards the ban) and must be tried again (<code>rootside.c</code>; the comment in <code>rootside.h</code> says it «waits»)."],
    ["Timing tail on a refusal", "If PAM's own delay exceeds the 2.5 s floor the answer time is no longer fixed."],
    ["Faillock detection", "The detection of <code>pam_faillock</code> works on English text only."],
    ["Quotas unmeasured", "The ban table (160 bans / 256 slots) and the unknown-user limit of 5 were not measured."],
    ["Kernel requirements", "Landlock needs kernel 6.12 (skipped on older ones), <code>mount_setattr</code> needs 5.12, "
     "the seccomp filter exists for x86_64 and aarch64 only (the aarch64 one was never run). The kernel of Ubuntu 26.04 is 7.0, so the requirement is met; the branch for an older kernel was not exercised in this tree."],
    ["Trust boundaries", "The root side is root and unconfined, and PAM modules run as root; users are separated by uid only; "
     "the product adds users to the card groups and puts ACLs on <code>renderD*</code>."],
    ["Power belts shipped off", "The logind power-key and no-suspend drop-ins are installed off, so the power button still works. The polkit rule is the only belt in force (19 actions)."],
    ["Needrestart", "The package installs a needrestart drop-in so that the service is never restarted by a library update (a restart closes every remote desktop, §11.56): the service is only listed for a manual restart, and the old library stays loaded until the administrator restarts it when no remote desktop is open."],
    ["Found-again desktop with a local session", "The network side does not close it (<code>found_again_close_for_local()</code>, "
     "<code>main.c</code>): the desktop leaves the list, so it has no cap count and no abandonment clock, and in the split server the root side "
     "ends its scope within about ten seconds. In the single-process mode (<code>--no-split</code>, not packaged) the process itself is root and closes that session with logind's <code>TerminateSession</code>; only if that fails is the stage left alone."],
    ["TERMINATE_SESSION", "Message 0x0011 is served, but nothing in the page sends it."],
    ["PACE", "The decoder pace message is dormant: the unit does not pass <code>--decoder-pace</code>, a PACE message is a violation, and "
     "RCP.md has no section for it."],
    ["Single-process mode", "<code>--no-split</code> is still in the code, with no walls and no coverage in <code>prove/</code>."],
    ["Clocks", "The 30 and 60 minute clocks were verified by mechanism at short values only (29 s and 90 s in the Ubuntu round). The dead line (10 s of silence) can detach before the 30 s silence clock."],
    ["Mounts after start", "Mounts made on the host after the network side starts arrive without the read-only bit."],
    ["Certificate and library pins", "The key-exchange fallback, the SETTINGS rewrite and the ngtcp2/nghttp3 pins must be re-tested at every upgrade. "
     "The congestion controller was never chosen (default CUBIC). The residual Stateless Reset limit is about 100 collected ids (<code>cid.h</code>)."],
    ["Session id in stream preambles", "Read and logged, never compared with the CONNECT stream id."],
    ["Closing a session before the stage is gone", "On GNOME, XFCE and LXQt the child tells the parent \"the session is over\" before it dismantles its stage (<code>session_over_early()</code>), only on a certain death. "
     "On KDE it does not: that road is left to a proof on a live machine, and the KDE desktop closes by the older road (the 10.9 s of the local login on Kubuntu)."],
], "«TAB» — Open points in the server.")

S_VIDEO = items([
    ["Dead AV1 code", "<code>encoder.c</code> still holds <code>read_av1_sequence</code>, OBU constants and <code>CODIFICATORE_AV1</code>; AV1 is not produced."],
    ["Shader header", "<code>vulkanvideo_rgb_nv12_spv.h</code> cannot be regenerated from the tree (the generator script is not in it)."],
    ["Budget, cap, quality rise, decoder pace", "All off and uncalibrated. <code>BUDGET_MAX_FPS</code> and <code>BUDGET_STRAIN_DELAY_MS</code> come from one GNOME/Intel UHD 770 machine; <code>WT_RATE_SLOTS</code> = 2 is uncalibrated."],
    ["No card or card that does not encode", "The error repeats every 2 s in the log. A new installation without a card is refused; with a card that does not encode it only says so. At start of a virtual machine the log shows a line \"CANNOT ENCODE VIDEO\" and about 2 s later \"the card arrived\": a race with the card's driver that resolves itself."],
    ["KDE and our labwc", "KDE does not use the system <code>labwc</code>: KWin is nested in our own, <code>/usr/libexec/remotix/labwc</code> (labwc 0.9.3 with a patched wlroots 0.19.2, static). If that file is missing KWin starts with <code>--virtual</code> and the desktop keeps the size it was born with (declared in the journal): the fallback was not re-tested on Ubuntu. "
     "KWin is 6.6.7 (Plasma 6.6); the system labwc stays for XFCE and LXQt. The upstream labwc and wlroots tarballs are fetched and checked by hash when the build image is made; the build itself needs no network."],
    ["Lost frames of KWin", "KWin sometimes drops a buffer. The cure is a \"poke\" (<code>kwin_poke()</code>), at most every 200 ms, only after a gap in the buffer numbering and never on a still desktop; the loss itself belongs to PipeWire and KWin and cannot be tuned from here."],
    ["Startup codec probe", "Uses the default <code>renderD128</code>; on two cards the encoding node is re-tested per session only when the nodes differ."],
    ["Encoded cursor theme", "Depends on a real cursor theme being installed; its effect on screen is unjudged."],
    ["HEVC", "Never reached the pixel on the test browsers: in the Ubuntu round the page's probe refused every HEVC string on Chrome and Firefox and every run negotiated H.264 (server log <code>media.out</code> of the round). On a real machine the server logged \"HEVC: yes via vaapi\"; in the virtual machines the video goes through Vulkan on the Radeon."],
], "«TAB» — Open points in capture and encoding.")

S_PAGE = items([
    ["Ctrl+Alt+Del button", "The button is hidden unless <code>?logbook</code> is in the address, by decision, and Ctrl+Alt+End reaches the desktop like any other combination. "
     "The checks were aligned to this on 18 Nov 2026 (<code>page-cad-hidden</code>, <code>page-ctrl-alt-end-passes</code>, register B3) and pass in the Ubuntu round; SPECS §7.3-bis and §5.2-bis still describe the old requirements. "
     "<code>run_logout()</code> exists but nothing calls <code>logout_show(true)</code>."],
    ["Firefox", "The video worker is the default on desktop Firefox without an isolated live proof. The Firefox clipboard checks pass in the Ubuntu round. The Firefox audio check was BLOCKED once by the test browser (Marionette did not answer) and passed on both repeats."],
    ["Keyboard layout and zoom", "No user-selectable keyboard layout (<code>navigator.language</code> is only a hint); a change of <code>devicePixelRatio</code> (page zoom) is not handled."],
    ["Test switches", "<code>?canvas=2d</code>, <code>?canvas=bmp</code>, <code>?draw=mse</code> and <code>#video_fault</code> remain; deleting the MSE path is undecided."],
    ["KDE", "A held Delete key is kept by the desktop (visible in diagnostics only). Klipper stops following above 10 changes a second."],
    ["Audio and clipboard", "No Safari or Windows Firefox; text only; no microphone. <code>SCHED_FIFO</code> may be refused with <code>CONFIG_RT_GROUP_SCHED</code>, so audio can crackle under load."],
    ["Opus decoder", "Nothing verifies that <code>page.html</code> embeds the current <code>opus.wasm</code>; <code>build.sh --verify</code> is run by hand only."],
    ["Window test and GTK 4.22", "The input test window reads the release from raw events because of the GTK 4.22 behaviour (register B3-bis); a check that fails the same on every desktop is first a suspicion on the tool."],
], "«TAB» — Open points in the page, input, audio and clipboard.")

S_DESK = items([
    ["XFCE", "Ignores a Log Out requested while the desktop is still starting (no retry in the code); a corner covered by the panel (mouse coordinates, register E2); the state file <code>xfce-chiavi</code> is not removed after the restore; an action button added by hand during a session is not locked until the next birth. "
     "The panel can lose its menu plugin in a few ways: <code>xfce_panel_integrity()</code> repairs the cases that were produced; two cases (the settings daemon restarted by hand during a local session, and a plugin node without a type held in memory) were never produced (study 9)."],
    ["GNOME", "Starts in the Overview and REMOTIX does not leave it; the Overview holds touches. The <code>SHELL</code> variable is deliberately empty in the composed environment (a trap of gnome-session's login shell, <code>session.c</code>); see the known limit on <code>pkexec</code>. "
     "On Ubuntu the Shell would warn \"Screen Lock disabled\"; the birth makes an empty file <code>~/.local/share/gnome-shell/lock-warning-shown</code> to prevent it, and the end of the session removes it only if the session's own sign says that REMOTIX made it. "
     "A user scale above 1 is brought back to 1 first (see the known limit)."],
    ["KDE", "Only KDE has the watch that finishes a Log Out systemd refused (<code>session_kde_logout_watch()</code>, now returning a boolean); the other desktops could in principle hit the same refusal, which was not investigated. Plasma 6.6 does not release the name that the older rescue waited for."],
    ["LXQt", "Whether <code>lxqt-session</code> logout without force works within 10 s is marked «[?]» in a comment. The X11 composition managers (<code>picom</code>, <code>compton</code>, <code>xcompmgr</code>) do nothing under labwc and are not started; <code>blueman.desktop</code> is hidden for XFCE and LXQt remote sessions; the <code>lubuntu-update</code> autostart entry is covered by one of our own."],
    ["Settings left behind", "Exceptions to «nothing permanent in the user's settings»: the XFCE copy and restore of locked keys, the LXQt one-time restore, and on Ubuntu the file <code>~/.config/dconf/remotix</code> (removed by <code>apt purge</code>). One-time cleanup marks (<code>gnome-ripristinato</code>, <code>lxqt-restored</code>, <code>xfce-vecchi-ripristinati</code>) remain for values of earlier versions. "
     "A <code>Hidden=true</code> entry hides the file name in whichever folder it is, so on XFCE a user's own visible <code>blueman.desktop</code> is not started either."],
    ["Environment variables", "<code>REMOTIX_VPP_PADDING</code> and <code>REMOTIX_VULKAN_CONVERSION</code> never reach a real session (the child environment is composed from scratch); they reach only the startup probe and <code>--encoding-test</code>."],
    ["Log priorities", "About 700 call sites starting with ⛔ were not observed in the priority run; their level is unverified."],
], "«TAB» — Open points in the desktops and logging.")

S_TEST = items([
    ["Rounds of 19 Nov 2026", "Full round on GNOME only: 120 PASS, 2 FAIL (<code>desktop/users-shell-and-environment</code>, a known limit; <code>ban/typed-names-not-logged</code>, a false red of the bench), 1 BLOCKED (Firefox audio), 3 SKIP (real login screen, other source addresses, package check). "
     "Earlier container rounds of 18 Nov 2026 (studies, first and second rounds) gave GNOME 123/124, KDE 121/124, LXQt 124/124 and XFCE 126/128 lines; those boxes no longer exist and were not the bench of the release. "
     "The other three virtual machines had a short start-up check with the Radeon, not the round. The bench was then changed to enter the machine as root, and only the ban and Firefox audio parts were run again."],
    ["Virtual-machine bench", "<code>RX_BANCO=vm</code> with <code>RX_TEMPO=2</code> (every deadline doubled); one machine at a time holds the graphics card; every client reaches the machine as the same address, so the check of other source addresses is a declared SKIP. "
     "The verdicts SKIP and NOTE are never a PASS; <code>all.sh --only a,b</code> repeats a part and ends with the line <code>PARTIAL RUN</code> and exit 3."],
    ["Package check", "<code>check-package.py</code> is not run by <code>all.sh</code> and not on the virtual machines; it was never run on Ubuntu 26.04 (studies 8 and 11)."],
    ["Check scripts", "<code>prove/fresh.sh</code> and <code>lib.py</code> look for <code>prove/boxes</code> and, if it is not there, for <code>../boxes</code>. "
     "<code>lib.sweep()</code> lists the prefixes of every check (<code>bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl</code>). <code>headless-multi.sh</code> and <code>lifecycle-window.py</code> have no caller. <code>base-check.py</code> and <code>check-base.py</code> are near duplicates."],
    ["Unit tests", "No in-tree tests exist for <code>hsrate.h</code>, <code>msgrate.h</code>, <code>linebudget.h</code>, <code>dimcheck.h</code>, <code>unchanged.h</code>, <code>damage_classify</code>."],
    ["Build", "A plain <code>make</code> in <code>src/</code> needs <code>TWIN=none</code>; <code>debian/rules</code> passes it. <code>SOURCE_DATE_EPOCH</code> defaults to file mtimes, so two checkouts differ; <code>build/build-deb.sh</code> takes the latest mtime of the tree it copies."],
    ["Clean-up", "Tranche 2 of the non-Debian clean-up is moot in this tree: the Ubuntu code it would have removed is live. Many identifiers are Italian (<code>registro_dice()</code>, <code>SORGENTI</code>, <code>wt_chi</code>, ...). A port to a distribution with SELinux needs the removed SELinux code again."],
], "«TAB» — Open points in testing and build.")

S_UBUNTU_OPEN = items([
    ["E3: the photo of the user manager's environment can be old, and \"could not look\" counts as \"closed\" (19 Nov 2026)", "When the root side closes a desktop (for example because the service stops), the photo of the user's manager environment taken before the session is not deleted. At the next session the clean-up still believes it, and may remove from the "
     "environment a variable that the administrator added in the meantime. The session is born right anyway, and without \"linger\" the environment is rebuilt at the next login (measured). Second point of the same family: the environment clean-up (<code>session.c</code>, near <code>session_alive()</code>) and the child's exit "
     "(<code>child.c</code>) treat \"I could not ask the desktop whether it is alive\" as \"it is closed\"; the dconf preparation was corrected on 19 Nov (three answers, <code>session_life()</code>), these two places were not. <b>Not corrected</b>: forced cases (an old photo together with linger and a failed birth; a live desktop that does not answer at that very moment), "
     "not producible on the bench. The suggested fix is small: the close made by the root side deletes the photo, and the two places use the three answers."],
    ["E4: small stutters in the video from Chrome on Android (19 Nov 2026)", "Seen by the owner while playing a 1440p and a Full HD video in the remote GNOME session of the Ubuntu virtual machine, from an Android phone; not seen from the tablet (Chrome on Linux). Measured on the server over 40 s of video towards the phone: no packet lost, 1.5 to 5 Mbit/s, 60 frames per second in 35 seconds out of 39 "
     "(the others 57, 56, 52 and 43), about one frame in twenty sent a few milliseconds late, network delay to the phone 8 ms typical with peaks to 125 ms (tablet: 3.5 ms, peaks 27 ms). <b>Cause not isolated</b>: the phone (Wi-Fi and the HEVC decode of Android), the video player in the virtual machine, the frame cadence of a virtual machine, or the encoding path on the Radeon. "
     "Non-blocking; no change made. To settle it: the same video from the tablet with the same measurement, and the same test on a real machine."],
    ["wireplumber warning on Ubuntu", "The owner saw an Ubuntu \"internal error\" warning, which is <code>wireplumber</code> stopping when the user's session ends (also after a normal exit from REMOTIX, seen at 21:50 on 19 Nov 2026). It was seen only on the virtual machine, which has no sound card, and not on the live images. Whether the missing sound card is the cause was not established. Non-blocking."],
    ["Autobind of abstract sockets", "The AppArmor profile allows \"autobind\": a socket that lets the system give it a random abstract name. It serves only to be reached by an accomplice process, not to reach the machine's sockets, and the second wall (Landlock) remains. To be looked at again when the profile goes from complain to enforce (register C4)."],
    ["KDE closing time at a local login", "On the live image of Kubuntu the remote desktop was closed by its child in 10.9 s at a local login (on GNOME 0.85 s). It is the known closing time of KDE (section D of the register) and one measurement; <code>session_over_early()</code> does not act on KDE. Nothing is lost, but a local user waits."],
    ["The dconf branches not tried", "\"Life unknown\" at the start of a child (new model and fallback) and \"database different or older\" at the start of the service were not tried in the field; the missing <code>dconf</code> and an administrator's <code>DCONF_PROFILE</code> in the child's own environment were approved by reading. Register C5, <i>Not proven in the field</i>."],
    ["Known limits of the dconf model (register C5)", "(1) A child that dies after the birth leaves the runtime file until the root side closes the orphan desktop; a local login of a user with no REMOTIX session known does not run the belt (low probability). (2) After a hot upgrade with a desktop born from the old model, a keyboard change does not reach it until the next birth; the old model was never shipped on Ubuntu. "
     "(3) At purge, users that the system does not list at that moment (an unreachable network directory) keep the small file, inert without REMOTIX."],
    ["What was not proven on Ubuntu", "A full round on Kubuntu, Xubuntu and Lubuntu (the round was run on GNOME only, by decision of the owner); a full round after the bench began to enter the machine as root; the local-login hold on a real login screen of Xubuntu and Lubuntu; the enforce mode of AppArmor; NVIDIA and an Intel card with GNOME 50; <code>check-package.py</code>."],
    ["From the studies, not re-checked", "The studies of the port (<code>studio/11-riscontro-studi-lavoro.md</code>, which predates the corrections of 19 Nov 2026) list points that were open then and that nobody re-read afterwards: " + sysf("user@UID.service") + " ending \"failed (timeout)\" after a Log Out because <code>mpris-proxy</code> does not stop (seen in the containers, not explained); "
     "<code>systemd-oomd</code> may kill the user manager, hence the remote desktop, under memory pressure (no code, no decision); <code>pam_motd</code> and <code>pam_sss</code> may slow the birth (not measured); the system <code>gnome-remote-desktop</code> and its \"Force Stop\"; a long idle time (15 to 20 minutes) on Xubuntu and Lubuntu; "
     "an application that really opens KWallet; variables and processes left behind with linger on; <code>ssh-agent</code> and <code>gpg-agent</code> possibly left in the scope after a Log Out on XFCE and GNOME; the key-stuck cure on Mutter 50; colour parity between Debian and Ubuntu; update-notification noise. They are listed as \"not re-checked\", not as open defects."],
], "«TAB» — Ubuntu: open points.")

CONTRA = [
    ["Unblock command", "SPECS.md:295,309; DECISIONS-11.md:1987,2002; main.c:245,3621; prove/check-ban.py header", "Describe an unblock command. The package ships none. page.c and page.html were changed to say the block ends by itself."],
    ["Fixed answer time", "SPECS.md §4.4; RCP.md §4.4-bis", "One fixed second. Code: 1000 ms for success, 0x08, 0x0E; REJECT_FLOOR 2500 ms for a PAM refusal (rcp.c:227-248)."],
    ["Paused AUTH", "rootside.h:290", "Says a paused request gets «not checked» and is not counted. Code answers RXR_PAUSED, a counted refusal 0x07."],
    ["fds crossing", "rootside_proto.h:19-27", "Says the child's socket end is the only fd that ever crosses. Code sends two with RXR_SPAWNED (the socket and a pidfd, rootside.c). The header now names RXR_CODEC."],
    ["PAM_RHOST", "sentinel.h:27", "Says never set. authentication.c and child.c:1675 set it."],
    ["Process limit", "walls.c:791", "Says 64 is wide. WALLS_NPROC_MAX is 128 (walls.h:71)."],
    ["/proc", "walls.h:45", "Says /proc is not hidden. The network side has its own /proc (main.c, rediscover_refuse_here)."],
    ["AppArmor", "remotix_network.apparmor:57", "The profile allows <code>network netlink raw</code> (marked «remove when proven unused») while seccomp refuses AF_NETLINK."],
    ["Stale installer text", "main.c:445-473; authentication.c:94; remotix.service:6; LICENSE.md:13", "Mention other distributions' PAM files (<code>.fedora</code>, <code>.suse</code>, <code>.arch</code>), «phases/17-the-installer.md», <code>--without split</code> / REMOTIX_SPLIT, and «the installer» (<code>remotix-*.run</code>). "
     "The text at main.c:466-473 is a <b>run-time log message</b> (" + "the PAM service «remotix» DOES NOT EXIST" + "): it should tell the administrator <code>apt install --reinstall remotix</code>; to be corrected at the next build."],
    ["Desktops survive the stop", "debian/rules:121; debian/remotix.postinst:11; debian/remotix.service:40; main.c:3967-3972", "Comments (and, in main.c, the log message «the network side stops — systemd restarts the unit, the desktops stay alive») say that the desktops stay alive "
     "when the service stops. Since 17 Nov 2026 (DECISIONS-11 §11.56) an orderly stop closes them, and after a fall of the root side the restarted root side ends them unless their user returns within about 10 s. To be corrected at the next build."],
    ["Debian-only wording", "CLAUDE.md; src/remotix.pam:1; src/local_login.c:20", "<code>CLAUDE.md</code> still names the tree <code>REMOTIX-DEBIAN</code> and says \"Debian 13 (trixie) only\", with a build line for <code>debian:trixie</code> and the paths of the Debian dev server, and the rule \"no distro detection\"; the first line of <code>remotix.pam</code> says «DEBIAN 13 ONLY»; "
     "a comment in <code>local_login.c</code> cites systemd 257. The tree is the Ubuntu 26.04 one (systemd 259.9); the manual does not repeat these as facts."],
    ["--session-fd", "DECISIONS-11.md §11.55", "Says the logind session is kept alive through <code>--session-fd</code> and a fifo. True for Debian 13 (systemd 257). This tree no longer passes it: since systemd 258 logind keeps the session by the pidfd of the leader, which is the child (a note of four lines in the same section says so)."],
    ["Paths", "debian/control; src/Makefile; build/quic-static.sh", "Name src/build-targets/quic-static.sh (now build/quic-static.sh), a <code>dipendenze</code> target (it is <code>deps</code>), benches scripts and provision.sh."],
    ["Licences", "CLAUDE.md", "Says licenses/ ships in the package; debian/rules installs only THIRD-PARTY-LICENSES."],
    ["Hooks", "rcp.h:164", "«Three, and no more»; about 27 exist."],
    ["Pending caps", "transport.h:129; hsrate.h:3", "Say 8 and 32. Code: PENDING_PER_ADDRESS 16, PENDING_PER_48 64."],
    ["Page caps", "page.h PAGE_MAX_CLIENTS comment; page.c", "Say 4 per address and a page of about 907 KB. Code: PAGE_PER_ADDRESS 32, PAGE_PER_48 64; the page is 937 399 bytes in this tree."],
    ["Keepalive", "rcp.c:8746 comment; webtransport.c keepalive_rule()", "Comment: PINGs only during credentials. Code: every state except finished."],
    ["Client close codes", "webtransport.c closed_by_client() ~7597; RCP.md §8.2", "Code accepts 0x01..0x0F; RCP.md and reason_for_82() up to 0x10."],
    ["Shutdown wait", "main.c ~4140", "Comment: two seconds. Loop: 4000 ms."],
    ["PACE", "DECISIONS-11 §11.32 title; comments citing RCP.md §13", "Title says on by default; body, rcp.h and main.c say off. RCP.md has no §13."],
    ["Encoder header", "encoder.c:2; child.c:7055-56", "Header names software and AV1; code has neither. Comment says hevc_strada, code prints hevc_route."],
    ["NVIDIA", "SPECS.md:1273", "Says nobody has seen NVIDIA work; comments cite measurements on an RTX 4090."],
    ["Bandwidth floor", "encoder.c, main.c, budget comments", "20 Mbit/s; WT_FLOOR_BYTE_MS is 3750 bytes/ms (webtransport.c:4018)."],
    ["Names", "wlroots.c; rcp.c comments", "RCP_TELA_L/A_MASSIMA for RCP_CANVAS_MAX_W/H; <code>tratta_*()</code> does not exist. SPECS names MAX_ATTACCATE, MAX_FIGLI, QUANTI_PRESENTI, WT_PALCHI, which are not in src/."],
    ["Logging", "log.h; log.c line()", "log.h: detail lines at priority 7; code never sends them to the journal. «Async-signal-safe» no longer true."],
    ["Settings comments", "session.c session_inhibit()", "LXQt panel entries «not touched» (six are hidden)."],
    ["Versions in comments", "session.h:216,230,245,264,274; shape.c:133", "Cite labwc 0.8.3 and lxqt-session 2.1.1; the Ubuntu boxes have labwc 0.9.3 and lxqt-session 2.3.0 (the code is right, the comments are old)."],
    ["GNOME 48 names in comments", "child.c:1682; rediscover.h:27; input.c:2075-2079", "<code>ConditionEnvironment</code> where GNOME 50 uses an <code>Assert</code> line; <code>gnome-session-binary</code> as the GNOME marker; «Mutter does not offer the lever» (GNOME 48 reading)."],
    ["Firefox worker", "page.html ~1318-1346, 9800-9803; DECISIONS-11 §11.36", "«Proposal, not decided»; code makes it the default; the decision is marked DECIDED."],
    ["Pointer mode, WebGL2", "page.html CSS 395-460; Viewer constructor ~3295", "<code>both</code> as default (code: <code>cl_mode = \"system\"</code>); WebGL2 «not the default» wording; <code>classic_input.hook()</code> (page.html:11411) does not exist."],
    ["Ctrl+Alt+Del", "SPECS §7.3-bis, §5.2-bis", "Require the button and Ctrl+Alt+End; the page hides one and removed the other. The checks of this tree follow the page."],
    ["Session survival", "SPECS §5.2 box", "Reports the T2 measurement of 29 Sep 2026: stopping the unit leaves the desktops alive. Since §11.56 (17 Nov 2026) an orderly stop closes them; SPECS was not updated."],
    ["Test windows", "check-media.py docstring; DECISIONS §4.6-septies", "250 ms (code 400 ms); UHD 730 (corrected to 770 in DECISIONS-11 §11.21)."],
    ["Polkit action count", "src/remotix-no-poweroff.rules (older paragraphs); DECISIONS.md §4.7; SPECS.md §A4", "The twelve or fifteen actions of earlier paragraphs are history: the rule now forbids nineteen (20 Nov 2026), and both documents say so in a dated update."],
    ["Missing files", "Comments in many headers", "Cite benches/, phases/, STUDIES.md, CODER.md, REVIEWER.md: not in this tree. main.c:3153 and :514 carry old wording."],
    ["PIANO.md", "PIANO.md", "The file of this tree is a summary of the Ubuntu work (the full history is in docs/STORIA-ubuntu-26.04.md), not the 1.0.0 Debian plan: the Debian statements about the unblock, the 8 users against RCP_SESSION_CAP = 10 and check-package 8/8 do not apply to it."],
]

S_CONTRA = table(["Subject", "Where", "What disagrees"], CONTRA,
                 "«TAB» — Contradictions between code, comments and documents (the code wins).")

CHAPTER = ("Appendix C — Known issues and open points", [
    ("How to read this appendix", S_INTRO),
    ("What is unverified", S_UNVERIFIED),
    ("Known limits and what was proven", S_LIMITS),
    ("Ubuntu: what real machines showed that the boxes did not", S_REAL),
    ("Open points in the server", S_OPEN),
    ("Open points in capture and encoding", S_VIDEO),
    ("Open points in the page, input, audio and clipboard", S_PAGE),
    ("Open points in the desktops and logging", S_DESK),
    ("Open points in testing and build", S_TEST),
    ("Ubuntu: open points", S_UBUNTU_OPEN),
    ("Contradictions between code, comments and documents", S_CONTRA),
])
