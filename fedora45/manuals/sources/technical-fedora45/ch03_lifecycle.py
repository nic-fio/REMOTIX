from build import arrow, box, c, fig, note, p, path, rif, seq, steps, sysf, table, text, tip, warn, zone

# ── Service start ────────────────────────────────────────────────────────
S1 = p("The service starts in two stages: the root side (" + rif("The root side") + ") does its own work and forks the "
       "network side, and the network side then runs the rest of " + c("main()") + ". Both write at startup what the "
       "machine can do and which values are in force, so that a missing piece is read in the log rather than discovered by "
       "the first user.", lead=True) + \
    p("<b>Before the root side</b>, systemd runs " + c("ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check") + " (" + c("rpm/remotix.service")
      + "): it checks that the block of the local-login hook is in the PAM files of the login screens and writes a line in the log; the dash means "
      "that it can never prevent the start (" + rif("The local-login hold") + " has the hook). <b>In the root side</b>, before the network side exists: the options are parsed; the network user is resolved once, "
      "as root (" + c("getpwnam()") + " of " + c("remotix") + "; if it is missing or is uid 0 the service exits with "
      + c("EXIT_CONFIG") + " = 78, which the unit's " + c("RestartPreventExitStatus=78") + " does not retry); the certificate "
      "folder, the ban file and the page must lie where the network side can use them (inside " + c("--network-state-dir")
      + ", and the page readable by " + c("remotix") + "), or the service also exits with 78 and says which option to fix; the "
      "UDP and TCP port are bound; then " + c("rootside_main()") + " makes sure the GNOME session's system dconf database is there "
      "(" + c("session_dconf_system_db_ensure()") + ", " + rif("The root side") + "), probes the card, sweeps the card ACLs of a "
      "previous run, starts the PAM dispatcher and the network side.") + \
    p("<b>In the network side</b>, in the order of " + c("main()") + ":") + steps([
        "<b>Born right.</b> " + c("network_side_born_right()") + " (" + rif("The network side and its walls") + "), then "
        + c("rootside_attach()") + " waits up to " + c("READY_WAIT_MS") + " (30 s) for " + c("RXR_READY") + ".",
        "<b>What is offered to the browser.</b> The codecs of the " + c("HERE_I_AM") + " are not measured here: " + c("READY")
        + " carries the root side's probe (" + c("child_video_capabilities()") + "). A machine with no card that encodes "
        "logs why, and every " + c("HELLO") + " ends in " + c("NOTHING_IN_COMMON") + " until a codec appears "
        "(" + rif("The card that arrives late") + "). On Fedora the usual cause is a machine without RPM Fusion's drivers: the log says "
        + c("THIS SERVER CANNOT ENCODE VIDEO") + " and the browser's request is answered " + c("NOTHING_IN_COMMON") + ". That is the requirement "
        "of PIANO D1, and the " + c("%post") + " scriptlet has already said so at the first installation (" + rif("Requirements and what Fedora adds") + ").",
        "<b>The desktop.</b> " + c("session_desktop_explain()") + " says which desktop this machine will start and why; on KDE "
        + c("kwin_check_permission()") + " checks that the " + c(".desktop") + " file that lets KWin offer screen capture to "
        "this binary is there (the package ships " + c("rpm/org.kde.remotix.desktop") + ", installed in " + sysf("/usr/share/applications/") + "). On XFCE and LXQt the explanation also "
        "says whether " + c("labwc") + " is installed: it is only a weak dependency of the package, and without it the log says that "
        "labwc is NOT there and the desktop cannot start. KDE does not need it: it runs on KWin alone.",
        "<b>The values in force.</b> The three clocks, the ghost-eviction threshold, the session cap, the budget, the queue "
        "threshold, the rate regulator, the dead line, the decoder pace: each is written with its value, <i>on or off</i>, "
        "so that a one-hour clock is verified by reading and not by waiting.",
        "<b>The log secret and the ban.</b> " + c("rcp_log_secret_load()") + " first (the ban file holds the HMAC of the names); "
        "then " + c("rcp_ban_load()") + ". If the ban file cannot be read the service exits with 1 rather than forget who "
        "was banned; “zero bans” and “could not look” are different facts.",
        "<b>The tables</b> of " + c("helper_turn_on()") + " (a proxy to the root side, in this process) and "
        + c("children_turn_on()") + " (sized on the cap), the optional bench socket (" + c("command_open()") + ", only "
        "with " + c("--command-socket") + "; the unit never gives it), the PAM file check (" + c("look_pam_service()")
        + "), the certificates (" + c("certificates_prepare()") + ": reads valid ones, generates otherwise) and the two TLS "
        "contexts.",
        "<b>The sockets.</b> " + c("transport_open_fd()") + " on fd 4 (UDP) and, after the next step, " + c("page_open_fd()")
        + " on fd 5 (TCP): the network side never binds.",
        "<b>The hooks</b> that tie transport, RCP and children together (video, audio, input, canvas, layout, pace, "
        "terminate, clipboard, local sessions); the sentinel (" + c("sentinel_open()") + "); and "
        + c("found_again_at_startup()") + ", which asks the root side for the desktops found again (waiting at most "
        + c("FOUND_AGAIN_WAIT_MS") + ", 3 s).",
        "<b>Ready.</b> The line “ready: https://name:port” is written and the loop starts. Every pass the loop reads the UDP "
        "socket, runs the abandonment clock, delivers PAM verdicts, moves the children, expires transport timers, moves the "
        "page sockets, sweeps local sessions every " + c("LOCAL_SWEEP_MS") + " (2000 ms), and every 60 s checks whether the "
        "session certificate needs rotating (" + c("certificates_rotate_if_needed()") + ").",
    ]) + \
    note("The first log line still reads “REMOTIX — phase 1, the bare wire”: it is the program's historical first line "
         "and the checks look for it. The comment at the top of " + c("main.c") + " also still describes phase 1 (“no "
         "video”); the code is the whole server.", "Old words, current code.")

S1B = p("A card whose render node appears only after the unit starts (late driver, firmware still loading, a GPU that "
        "comes up after boot) would otherwise leave the service refusing every " + c("HELLO") + " for as long as it ran. "
        "When the startup probe finds no codec the root side keeps measuring (" + c("codec_retry()") + " in "
        + c("rootside.c") + "):", lead=True) + \
    table(["Case", "What the root side does"], [
        ["The card's node is missing", "Probes again 2 s later, then at doubling intervals up to 60 s, until the node opens "
         "(" + c("codec_every_ms") + " starts at 2000)"],
        ["The node opens but nothing encodes", "The same schedule, but it stops when " + c("child_video_retry_worthwhile()")
         + " says it is not a matter of time (five tries, about a minute), and logs “fix the card or its driver and restart”"],
        ["The node is there, the codec is not (the usual case on Fedora)", "A node opens but nothing encodes because the machine has no RPM Fusion driver (" + sysf("mesa-va-drivers-freeworld") + "): "
         "this is the second row, and the schedule is the same. The remedy is the administrator's: install the driver (PIANO D1), then restart the service (" + c("sudo systemctl restart remotix") + "): in this case the retry stops after about a minute and does not look again "
         "(" + c("sudo /usr/libexec/remotix/remotix --encoding-test h264") + " tells at once whether the card encodes)"],
        ["A probe finds codecs", "It sends " + c("RXR_CODEC") + " (" + c("offered") + " and " + c("explanation") + "); the "
         "network side's hook " + c("codec_from_root()") + " sets " + c("video.codec") + " for the next " + c("HERE_I_AM")
         + ". A network side started afterwards gets the result in " + c("READY") + "; the network side also asks "
         "again when a " + c("HELLO") + " finds the list empty (" + c("rcp_video_codec_retry_hook()") + ")"],
    ], "«TAB» — A card that arrives after startup") + \
    p("On a machine with no card at all the package refuses a <i>new</i> installation (the " + c("%pre") + " scriptlet of " + c("rpm/remotix.spec")
      + ": nothing named " + c("renderD*") + " in " + sysf("/sys/class/drm") + "; " + rif("The package") + "), so this case matters for a card that is present but late, or for an upgrade.")

# ── Unit ────────────────────────────────────────────────────────────────
S2 = p("The service is the system unit " + c("rpm/remotix.service") + ", installed by the spec and handled by the scriptlet macros " + c("%systemd_post") + ", "
       + c("%systemd_preun") + " and " + c("%systemd_postun_with_restart") + ": the package puts the unit there but does not enable or start it (the Fedora preset is "
       + c("disable *") + ": the administrator runs " + c("systemctl enable --now remotix") + "), and an upgrade restarts it only if it was already "
       "running (the restart closes the remote desktops, see "
       + rif("Stopping the service") + "). The settings that shape the life cycle:", lead=True) + \
    table(["Setting", "Value", "Why"], [
        [c("Type"), c("simple"), "the root side is the main process; " + c("exec") + " in the " + c("ExecStart") + " shell keeps it so"],
        [c("After="), c("network.target") + " and " + sysf("systemd-logind.service"), "logind must be there for sessions and for the sentinel"],
        [c("KillMode"), c("mixed"), "SIGTERM to the root side only, then SIGKILL to what is left of the unit; the desktops "
         "are outside the unit (" + c("setsid --fork") + "), so the unit's own kill does not reach them: the root side "
         "closes them itself at an orderly stop (" + rif("Stopping the service") + ")"],
        [c("Restart"), c("on-failure") + ", " + c("RestartSec=2"), "a crash restarts the root side, which ends the desktops left without a child, unless their user returns "
         "within about 10 s (" + rif("Desktops found again after a restart") + ")"],
        [c("RestartPreventExitStatus"), c("78"), "a configuration error (" + c("EXIT_CONFIG") + ") is not retried"],
        [c("LimitRTPRIO"), c("20"), "priority for audio and video threads"],
        [c("LimitNICE"), c("-11"), "the same"],
        [c("Environment"), c("MESA_SHADER_CACHE_DISABLE=true"), "the root side's probe of the card would open Mesa's shader cache in " + sysf("/root/.cache") + ", and its SELinux domain has no type for it; the "
         "cache is useless to a probe that runs once. Only the service's own environment: the users' desktops get theirs from PAM and keep the cache"],
        [c("ExecStartPre"), c("-/usr/libexec/remotix/remotix-pam-hook check"), "checks at every start that the block of the local-login hook is in the PAM stacks of the login screens and applies it again if not; "
         "the dash means that the start is never prevented"],
        [c("User="), "not set", "the unit runs as root; hardening is in the program (" + rif("The network side and its walls") + ")"],
        [c("EnvironmentFile"), c("/usr/share/remotix/remotix.conf") + " then " + c("/etc/remotix/remotix.conf.d/*.conf"),
         c("REMOTIX_PORT") + " (7447) and " + c("REMOTIX_OPTIONS") + " (empty); the last " + c("--name") + " wins"],
    ], "«TAB» — The unit's settings that matter for the life cycle") + \
    warn("Some comments of the package's files are stale. The header of the unit mentions a build made with " + c("--without split")
         + " (" + c("rpm/remotix.service") + ", line 6) that this tree does not have; " + c("rpm/remotix.conf") + ", "
         + c("rpm/remotix-no-suspend.conf") + " and " + c("rpm/remotix.tmpfiles") + " still speak of “the engine”, a program "
         "that is not in this tree. The comment on " + c("KillMode") + " in " + c("rpm/remotix.service") + " and a comment of the " + c("%post")
         + " scriptlet of the spec (“the desktops stay alive”) still say that the desktops survive the stop (SPECS §5.2): "
         "since the decision of 17 Nov 2026 (" + c("DECISIONS-11") + " §11.56) an orderly stop closes them. The settings in the "
         "table are those in force; the comments are to be corrected at the next build.", "Old comments in the unit.")

# ── Login ────────────────────────────────────────────────────────────────
LOGIN = seq([("Page", "browser", "light"), ("Network side", "user remotix", "navy"), ("Root side", "root", "navy"),
             ("PAM check", "root, one per try", "dark"), ("Child", "the user", "blue")], [
    (0, 1, "HELLO · CREDENTIALS"),
    (1, 2, "AUTH + password + address"),
    ("note", 2, "bounds, pauses"),
    (2, 3, "check request"),
    (3, 2, "one byte", True),
    (2, 1, "VERDICT + one-time grant", True),
    ("note", 1, "refusals before fork"),
    (1, 2, "SPAWN (grant, canvas)"),
    (2, 4, "fork · PAM session · exec"),
    (2, 1, "SPAWNED + socket + pidfd", True),
    ("sep", "not before one second after CREDENTIALS (2.5 s for a refusal)"),
    (1, 0, "ADMITTED"),
    (0, 1, "ATTACH (canvas, layout)"),
    (1, 4, "canvas · video on"),
    (4, 1, "stage · frames", True),
    (1, 0, "SESSION, then video"),
], "«FIG» — From password to admission: five processes, in the order of the events")

S3 = p("A login crosses five processes. Only the order and the numbers are given here; the protocol is in "
       + rif("The RCP/1 protocol") + " and the defences in " + rif("Login and its defences") + ".", lead=True) + LOGIN + \
    steps([
        "<b>Deadlines of the handshake</b> (RCP.md §4.6, constants in " + c("rcp.c") + "): " + c("HELLO") + " within "
        + c("CAP_HELLO") + " = 5000 ms of the control channel opening, " + c("CREDENTIALS") + " within " + c("CAP_CREDENTIALS")
        + " = 60 000 ms of " + c("HERE_I_AM") + " (a person types), " + c("ATTACH") + " within " + c("CAP_ATTACH")
        + " = 10 000 ms of " + c("ADMITTED") + ". While it waits for the credentials the server keeps the connection alive "
        "with transport PINGs, or the 30 s QUIC idle timeout would end it before the 60 s.",
        "<b>The check.</b> The network side sends " + c("RXR_AUTH") + "; the root side applies its bounds, refuses names that "
        "are uid 0, listed or unknown, applies its three pauses, and only then asks the PAM dispatcher. The answer is a "
        + c("RXR_VERDICT") + " with an outcome and, for a yes, a 16-byte grant valid " + c("RXR_GRANT_LIFE_MS") + " (30 s) "
        "and the system's canonical spelling of the name.",
        "<b>The answer is never early.</b> " + c("FIXED_DELAY") + " (1000 ms) after the credentials arrived for every answer; "
        + c("REJECT_FLOOR") + " (2500 ms) for a refusal that goes out as " + c("0x07") + ", so that the time does not "
        "tell a name in the denied list, a wrong password and an unknown name apart. A verdict that has not arrived after "
        + c("VERDICT_CAP") + " (12 000 ms) is a no; the helper's own expiry is " + c("EXPIRY_MS") + " (8000 ms).",
        "<b>Admission</b> (" + c("delivery_verdict()") + " in " + c("main.c") + "), in this order, each a refusal that "
        "leaves no process behind: a local graphical session of that user, or logind not saying, before any birth (" + c("0x05")
        + " or " + c("0x0E") + ", fail-closed); the previous desktop of that user still closing (" + c("0x0E") + "); the "
        "<b>compositor not installed</b> (" + c("session_missing_component()") + ": XFCE or LXQt without " + c("labwc") + ", "
        + c("0x0E") + " with the sentence “the desktop (…) cannot start: `labwc` is not installed on this server”, for a login "
        "that is not a resume; the log names the package, and the " + c("%post") + " scriptlet has said " + c("sudo dnf install labwc") + "; nothing is born); "
        "<b>a KDE session that cannot be used</b> (" + c("0x0E") + ", “this KDE session cannot be used”: KWin does not offer " + c("kde_output_management_v2") + ", " + rif("KDE: KWin alone")
        + "); <b>a SELinux refusal</b> (the child exits with 44, 45, 46 or 47, or with 37 when the policy forbids the exec, as for a user mapped to " + c("sysadm_u") + " (REGISTRO F31), and the birth fails: " + rif("The per-user child") + "); the "
        "stages of the server all in use (" + c("stage_count()") + " not below " + c("rcp_cap()") + ", " + c("0x0E") + "); "
        "the budget (" + c("has_capabilities()") + ", " + c("0x06 BUDGET_FULL") + "); then the birth.",
        "<b>The birth.</b> " + c("children_ensure_from()") + " sends " + c("RXR_SPAWN") + " with the grant and waits up to "
        + c("SPAWN_WAIT_MS") + " (15 s: at a user's first login the birth may include " + c("usermod") + ", itself bounded to "
        "5 s; on Fedora 45 the render node is open to everybody, so this step probably has nothing to do, which has not been verified). The root side checks the grant, the name, that no child of that uid exists, the cap, and that the canvas "
        "is within 320×240 and 4096×2304 (else it uses its own 1920×1080), runs " + c("child_birth()") + " and answers "
        + c("RXR_SPAWNED") + " with the child's socket end and a pidfd. A refusal is an " + c("rxr_refusal") + " code that "
        "the network side turns into a sentence.",
        "<b>ADMITTED and ATTACH.</b> Only now does " + c("ADMITTED") + " go out. " + c("ATTACH") + ", in the order of the code, "
        "reduces a canvas above " + c("RCP_CANVAS_MAX_W") + "×" + c("RCP_CANVAS_MAX_H") + " (4096×2304) with a logged fallback, "
        "refuses one below " + c("RCP_CANVAS_MIN_W") + "×" + c("RCP_CANVAS_MIN_H") + " (320×240) or with an odd side with "
        + c("0x0B PROTOCOL_ERROR") + ", asks the sentinel once more for a "
        "local session (" + c("0x05") + ", also when logind could not say), takes the attach slot (" + c("slot_take()") + "; if another live client of that user "
        "holds it and is not evicted as a ghost, " + c("0x0F ALREADY_ACTIVE_REMOTELY") + "), "
        + "asks the stage for that canvas (the canvas granted can differ from the one asked for: the stage may already have another size, RCP.md §4.5), and answers " + c("SESSION")
        + " with state 1 (NEW) or 2 (RESUMED, the stage was already there).",
    ]) + \
    p("<b>Who is told when a session ends.</b> The farewell of a session that is over (" + c("0x10") + ", or " + c("0x0E")
      + " for a refused stage) does not go to every connection that carries the user's name: " + c("wt_dismiss_user_session_over()")
      + " in " + c("webtransport.c") + " tells the connections that are logged in at once; a connection that was ADMITTED but is "
      "still inside the fixed second (" + c("rcp_admitted_waiting()") + ") gets the same farewell held until that second has "
      "passed, in the place of ADMITTED; a connection still waiting for PAM, or whose refusal is being held, is skipped, because "
      "it was never attached to that session and must learn nothing about the account (RCP.md §4.4). Before 19 Nov 2026 all three "
      "kinds were told at once, and a login refused with 0x0E “still closing” received a false 0x10.") + \
    tip("None of the admission checks forks a process: a user refused for a local session, a full cap or the budget costs no "
        "child. A desktop found again of a user who then opens a local session is not closed by the network side (it is "
        "user " + c("remotix") + ", and only the root side may end a logind session): it leaves the list (" + c("found_again_close_for_local()")
        + " says so in the log, “the root side ends its scope by itself”), and the root side ends its scope within about "
        "10 s; the local-login hook (" + c("remotix-pam-hook") + " puts it in the PAM stack of gdm, plasmalogin, lightdm and sddm) does it before the local desktop starts (" + rif("The local-login hold") + ").",
        "Refuse before forking.")

# ── Birth ───────────────────────────────────────────────────────────────
S4 = p("The child is born before it knows the window's size, and it must not start the desktop at the wrong size: on "
       "Wayland a resize completes only when the compositor delivers a frame, and a freshly started desktop that does not "
       "move never does. So the child waits for the client's canvas before making anything be born, with a ceiling.",
       lead=True) + steps([
        "<b>Introduction.</b> " + c("child_alive()") + " sends " + c("MSG_INTRO") + " (who it is: uids, gids, pid, open "
        "descriptors, the runtime folder, whether the session bus socket exists) and the network side checks it against "
        "the kernel's stamp. A non-answer within " + c("SHOW_UP_DEADLINE_MS") + " (15 s) kills the child.",
        "<b>Waiting for the canvas.</b> " + c("take_stage()") + " answers “waiting for the client's canvas” (a " + c("MSG_STAGE")
        + " with an unread session state) for up to " + c("CANVAS_WAIT_MS") + " (1200 ms) while the client's " + c("ATTACH")
        + " carries its window size to the child as " + c("CHILDREN_INPUT_RECANVAS") + ". If none comes, the child starts at "
        "the fallback canvas and says so.",
        "<b>The desktop.</b> " + c("session_ensure()") + " (or the non-blocking " + c("session_spawn()") + ") asks whether the "
        "session exists and has the right monitor. If the session is dead it starts one with " + c("setsid --fork sh -c") + ": "
        "the desktop is detached from the child's process group, which is why it survives the child. An orderly stop of "
        "the service closes it (" + rif("Stopping the service") + "). Its output goes to " + c("~/.local/state/remotix/session.log") + " (the user's state folder). The start "
        "command is the desktop's own. <b>GNOME:</b> the " + c("Exec") + " line of the GNOME session the machine offers, chosen "
        "by the rule D8 (DECISIONS §10.20): the only " + c("gnome-session") + " session found in " + c("wayland-sessions") + ", else "
        "the one bearing the distribution's name (" + c("ID") + " of " + sysf("/etc/os-release") + "), else " + c("gnome") + ". On "
        "Fedora 45 the sessions offered are " + c("gnome") + " (" + c("Exec=/usr/bin/gnome-session") + ", " + c("DesktopNames=GNOME") + ") and " + c("gnome-classic")
        + ", none is called " + c("fedora") + ", so the choice is " + c("gnome") + " and " + c("XDG_CURRENT_DESKTOP") + " is " + c("GNOME") + " (study 1). "
        "The Shell's unit is overridden to start headless (below). <b>KDE:</b> " + c("startplasma-wayland") + ", with a drop-in on "
        + sysf("plasma-kwin_wayland.service") + " that sets " + c("REMOTIX_KDE_HOST=1") + " and whose " + c("ExecStart") + " is " + c("remotix --kwin-virtual W H -- "
        "kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen") + " (" + rif("KDE: KWin alone") + "). <b>XFCE and LXQt:</b> " + c("xfce4-session")
        + " or " + c("lxqt-session") + " on the distribution's own labwc (" + rif("The four desktops") + "). The " + c("PATH") + " "
        "and the language words of the session are those described in " + rif("The per-user child") + ". On GNOME 51 the guard of GNOME 50 still applies "
        "(study 1 found that " + c("gnome-session-init-worker") + " aborts if the remote session is “closing”; that it is identical to GNOME 50 has not been verified): " + c("gnome-session") + " refuses to start while " + sysf("graphical-session.target") + " of the user "
        "manager is still active, so " + c("inactive_unit()") + " counts it, with the session manager's unit and the D-Bus "
        "restart unit, among the things that must have ended: a birth too close to the end of the previous session says no, and "
        "the child's retry loop asks again a moment later.",
        "<b>Retries.</b> If the stage is not there yet the child retries every " + c("STAGE_BIRTH_RETRY_MS") + " (200 ms) inside "
        "a window of " + c("BIRTH_REIN_MS") + " (12 s) after asking for the session's birth, then at " + c("STAGE_RETRY_MIN_MS")
        + " (1000 ms) doubling to " + c("STAGE_RETRY_MAX_MS") + " (30 s); a blocking " + c("session_ensure()") + " waits at most "
        + c("WAIT_STARTUP_MS") + " (40 s). The child does not exit when there is no stage: §8.3 of SPECS forbids disconnecting; "
        "it logs a heartbeat once a second.",
        "<b>The stage.</b> The virtual monitor, the capture stream, the input device (libei on Mutter and KWin, virtual "
        "devices on labwc), the clipboard and the audio sink are mounted by " + c("take_stage()") + "; the child reports the "
        "result in " + c("MSG_STAGE") + " and, once the first frame is seen at the right size, " + c("MSG_CANVAS") + ".",
    ]) + \
    p("<b>The logind session.</b> Before dropping privileges the child opens a PAM session (service " + c("remotix") + ", type "
      "wayland, class user, no seat) and calls " + c("pam_end()") + " without closing it. Since logind 258 the session is held by "
      "the pidfd of its leader, which is the child (the process that opened it, with the same pid after the " + c("execve()")
      + "), so nothing is carried across the " + c("execve()") + " and the logind session lives exactly as long as the child "
      "(Fedora 45 has systemd 262; an older logind is not supported). A desktop's processes are in that session's scope. "
      "A session without a seat is headless, which on GNOME is the only form in which the screen locker does not revoke the "
      "capture (" + c("sentinel_without_seat()") + " verifies it after startup). " + rif("The per-user child")
      + " has the details of the fork.") + \
    note("On GNOME 51 the Shell is the template unit " + sysf("org.gnome.Shell@.service") + " (" + c("SESSION_UNIT_SHELL_MODEL")
         + " in " + c("session.h") + "; on the Fedora machine its own " + c("ExecStart") + " is " + c("gnome-shell --mode=user") + ", study 1). The instance is the one "
         "the chosen session asks for: " + c("gnome") + " gives " + sysf("org.gnome.Shell@user.service") + ". " + c("unit_shell()") + " reads it from the " + c("Requires") + " of "
         + sysf("gnome-session@<session>.target") + ", asking the user manager. The drop-in that removes the monitors of the "
         "Shell's own is written at every birth into the folder of the <b>instance</b> (its " + c("ExecStart") + " is " + c("gnome-shell --headless --no-x11 --mode=%i")
         + "), never into that of the template (a "
         "drop-in on " + sysf("org.gnome.Shell@.service.d/") + " would also apply to the Shell of the login screen), and is "
         "verified, because a line that can be lost is not a protection (invariant I7).", "GNOME 51.")

KDE = p("KDE on Fedora 45 runs on <b>KWin 6.8 alone</b>: no second compositor and no patched labwc (PIANO D2, REGISTRO F7). The owner's reason "
        "is that the code travels between the distributions, and Debian and Ubuntu will find it written and tried when they have KDE 6.8.",
        lead=True) + steps([
        "<b>Birth.</b> The child writes the drop-in on " + sysf("plasma-kwin_wayland.service") + " (" + c("session.c") + ") and starts " + c("startplasma-wayland")
        + ". The drop-in sets " + c("REMOTIX_KDE_HOST=1") + " and runs " + c("remotix --kwin-virtual W H -- kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen")
        + ": the server's own binary starts a very small service that answers " + sysf("org.freedesktop.ScreenSaver") + " and then becomes the KWin wrapper "
        "(" + c("kwin_virtual_alive()") + "). The two marks, " + c("--kwin-virtual") + " on the command line and " + c("REMOTIX_KDE_HOST=1") + " in the environment, "
        "are how REMOTIX later knows that this KWin is its own (" + c("kdehost.h") + ").",
        "<b>Size.</b> " + c("--width") + " and " + c("--height") + " count only the first time: KWin remembers the last mode of its output " + c("Virtual-0") + " in "
        + sysf("~/.config/kwinoutputconfig.json") + ", a file of KWin that REMOTIX never touches (REGISTRO F8), and a later session may be born at that size. So the child "
        "checks the size and corrects it, <i>before</i> it mounts the stream, with " + c("kwin_output_resize()") + ": the Wayland protocol " + c("kde_output_management_v2")
        + " (version 22 or later) and a custom mode, any size, odd ones too, in about 3 ms. The stream does not follow a change of size: it is dismounted, the output changes, "
        "and it is mounted again.",
        "<b>If KWin refuses.</b> A KWin without the protocol (older than 6.8): <b>the session is refused</b>, with one line in the log (“⛔ KDE: SESSION REFUSED, and closed”), the clients get "
        + c("0x0E") + " and the graphical session is closed by the road of the scale refusal; no silent fallback and no endless retry (REGISTRO F13). "
        "KWin or its output not ready yet: it tries again, one log line every 5 s. KWin that answers “no” or does not answer: the stage is mounted at the size KWin has, with the line "
        "“⚠ KDE: KWin's output did not reach WxH … DECLARED FALLBACK”, and the page rescales; a black screen would be worse. Known limit: a KWin that takes longer than 3 s at birth starts "
        "that fallback, and the size stays old until the next reattach.",
        "<b>The size changes only at birth and at reattach.</b> The product asks the desktop for the window's size only then. Resizing the browser window of a live session never changes "
        "the desktop on any desktop: the page rescales the image (REGISTRO F14, DECISIONS §5.1-bis). On KDE this was tried: 8 resizes in a row, odd sizes included, and the desktop stays at its size "
        "(" + c("prove/check-kde-live.py") + ").",
        "<b>The end.</b> A forced close of KDE stops " + sysf("graphical-session.target") + " (" + c("StopUnit") + " in mode “fail”), which takes KWin, ksmserver and plasmashell down together, in about "
        "0.5 s (REGISTRO F36). In a local-login close the orderly step waits 5 s, not 10 (" + rif("Ending a graphical session") + ").",
    ]) + \
    p("<b>Said as not verified.</b> With several graphics cards KWin chooses its own render device: the bench has one Radeon, so this was not tried with two (REGISTRO F12). "
      "The shape and place of the cursor after a change of size was looked at on the bench and is still to be looked at on a real screen (REGISTRO F11).")

S5 = p("Detaching is the normal end of a connection, and it ends nothing else: the slot frees and the stage stays "
       "(invariant I4). Three things can detach a client, and the farewell differs:", lead=True) + \
    table(["Cause", "What the server does", "Constant"], [
        ["The client closes the page, the browser or the network drops cleanly", "The connection ends; the slot is freed; "
         + c("release_on_detach()") + " lifts every key and button still down (" + c("CHILDREN_INPUT_RELEASE_ALL") + ")",
         "—"],
        ["The client is silent for 30 s", "The session becomes " + c("S_DETACHED") + " (“DETACHED for silence”), the slot is "
         "freed, keys released, the connection is <i>left open</i>: if the client speaks again it takes the slot back if free. "
         "The clock looks at the last authenticated packet, not at user input", c("SILENCE") + " (30 000 ms) in " + c("rcp.c")],
        ["The client is silent and a new one of the same user arrives", "The newcomer evicts the ghost if its silence is at "
         "least the threshold, never across users. The threshold is half the silence clock; " + c("--eviction-ms 0")
         + " switches it off", c("DEFAULT_EVICTION") + " (15 000 ms)"],
        ["Stalled output or long silence", "The dead line detaches the connection when frames are owed and nothing leaves, or the "
         "client says nothing; on by default; " + c("--no-dead-line") + " switches it off ("
         + rif("Quality, degradation and budget") + ")", c("WT_LM_STALL_MS") + " (5000 ms), " + c("WT_LM_SILENCE_S") + " (10 s)"],
        ["30 minutes without input", "A farewell " + c("0x02 INACTIVITY") + ": the page returns to the login form, user and "
         "password are needed again; the desktop stays", c("DEFAULT_INACTIVITY") + " (1 800 000 ms)"],
    ], "«TAB» — What detaches a client") + \
    p("When the last client detaches, the network side asks the child to turn the video and audio off (codec 0, "
      + c("MSG_VIDEO") + ", " + c("MSG_AUDIO") + "): the capture stops, the virtual monitor and the audio sink stay. "
      "<b>Reattaching</b> is a normal login: the user is checked again, a child already exists for that uid (so no birth), "
      "the attach asks for the new window's canvas, the child resizes the desktop and starts a keyframe, and " + c("SESSION")
      + " says RESUMED. The page returns to the same windows and text. " + c("prove/check-lifecycle.py") + " verifies it "
      "three ways on each desktop (clean close, a browser killed with -9, and a smaller window on return), and "
      + c("prove/check-resilience.py") + " verifies a network drop longer than the silence clock.") + \
    warn("The silence clock is 30 s in the code and in SPECS §5.3, but the dead line (on by default since 24 August 2026) "
         "can end a connection earlier: after " + c("WT_LM_SILENCE_S") + " (10 s) of client silence while the server has "
         "something to send. The stage is not touched either way. " + c("prove/check-resilience.py") + " names both numbers "
         "(“spec 30 s; code 10 s dead-line”).", "Two clocks look like one.")

# ── Found again ─────────────────────────────────────────────────────────
S6 = p("Only a fall of the service (a crash, a SIGKILL) or of the network side leaves a desktop with no process that "
       "watches it. The root side ends such a desktop within about 10 s (it must be seen in two scans of "
       + c("LX_EVERY_MS") + " = 5 s in a row: “no orphan desktops”); a user who comes back before that finds it again "
       "(RESUMED), and after that the next login is NEW. An <b>orderly</b> stop closes every desktop (" + rif("Stopping the service")
       + "), so there is nothing to find after it. The mechanism below (" + c("rediscover.c") + ", " + c("FOUND_*")
       + ") still runs at every start of the network side, but it now describes a window of a few seconds, not a normal outcome. "
       "Until 17 Nov 2026 (" + c("DECISIONS-11") + " §11.56) a stop left the desktops alive for the reattach; the owner decided "
       "that they are closed because an orphan desktop breaks the local login of the same user on GNOME's login screen.",
       lead=True) + \
    p("<b>The criterion</b> (" + c("rediscover.h") + "), the same for all desktops: a logind session with " + c("Service=remotix")
      + ", in any state (it is “closing” as soon as its leader, the child, is gone, which is the case after "
      "a fall of the service; the comment in " + c("rediscover.h") + " still describes the behaviour before 17 November "
      "2026, when it was “closing” a moment after birth), that contains a process of the user which is leader of its own process session (pid equals sid) and whose "
      "parent is not in the same scope. That is the signature of " + c("setsid --fork") + ": the session's starter (" + c("gnome-session") + " on GNOME; on Fedora 45 its process chain is "
      + c("gdm-wayland-session") + " then " + c("gnome-session-init-worker") + ", and the exact process name that the criterion meets there has not been verified), "
      + c("startplasma-wayland") + " or " + c("labwc") + ". A terminal opened inside the desktop does not match, because "
      "its parent is in the scope.") + \
    table(["Step", "Where", "What"], [
        ["Search", c("found_look()") + " in " + c("rootside.c"), "Before every start of the network side the <b>root side</b> lists "
         "them: it reads logind's own files " + c("/run/systemd/sessions/<id>") + " and " + c("/proc") + " ("
         + c("rediscover_search_files()") + "), with no GLib. The network side never reads either: "
         + c("rediscover_refuse_here()") + " makes " + c("rediscover_search()") + " refuse there"],
        ["Tell", c("found_pump()"), c("RXR_FOUND_AGAIN") + " × N, then " + c("RXR_FOUND_END") + " (count N), then later "
         + c("RXR_FOUND_GONE") + " for any that dies"],
        ["Watch", c("found_watch()"), "Each stage is watched by a pidfd and its start time (field 22 of " + c("/proc/<pid>/stat")
         + "), so a reused pid is another process; without " + c("pidfd_open") + " the start time is read again every "
         + c("FOUND_POLL_MS") + " (10 s)"],
        ["Count", c("found_again_at_startup()") + " in " + c("main.c"), "The network side waits at most " + c("FOUND_AGAIN_WAIT_MS")
         + " (3 s), puts each desktop in a table (at most " + c("MAX_FOUND_AGAIN") + " = 256) and starts its abandonment clock "
         "<b>from now</b>: the last gesture seen by the previous process was in its memory. The cap and the budget count them "
         "(" + c("stage_count()") + ")"],
        ["Return", c("delivery_verdict()"), "When the user logs in, a new child is born (" + c("ensure_from_clearing_mark()")
         + "); it finds the same desktop; " + c("SESSION") + " says RESUMED; the table entry is removed"],
        ["Abandon", c("abandon_expired()"), "If nobody returns within the abandonment time, a <i>close-only</i> child is born "
         "(" + c("RXR_CLOSE_ORPHAN") + ", no password) to close it (" + rif("Ending a graphical session") + "). In the split "
         "server the root side's own rule (“no orphan desktops”, above) ends a desktop without a child much earlier"],
    ], "«TAB» — Desktops found again, step by step") + \
    p("If the search cannot look (the sessions directory or " + c("/proc") + " unreadable) the outcome is " + c("RXR_FOUND_UNKNOWN")
      + " and the network side counts nothing, and says so: found desktops then count for neither cap, budget nor clock. If "
      "more desktops are found than the cap allows, no new user gets in until they leave, but each of those users gets back "
      "into their own. A restarted <i>network side</i> alone is told the table as the root side still has it.") + \
    note("The network side's repeated search (the whole question every 10 s, " + c("FOUND_AGAIN_SWEEP_MS") + " in " + c("main.c")
         + ") is the single-process mode's; in the split server " + c("found_again_sweep()") + " returns at once and "
         + c("RXR_FOUND_GONE") + " says when one dies.", "Split server.")

# ── Clocks ──────────────────────────────────────────────────────────────
S7 = p("Clocks run on scales from milliseconds to an hour. Each one is listed with the constant that holds it, the file, and "
       "what it ends. Values are those of the code today; options move some of them, and the value in force is written in the "
       "log at startup.", lead=True) + \
    table(["Clock", "Value", "Constant, file", "What it ends"], [
        "Session clocks (SPECS §5.3)",
        ["Client silence", "30 s", c("SILENCE") + ", " + c("rcp.c"), "the client is detached; the slot is freed"],
        ["Ghost eviction", "15 s", c("DEFAULT_EVICTION") + ", " + c("rcp.c"), "a silent client's slot goes to a newcomer of the same user"],
        ["User inactivity", "30 min", c("DEFAULT_INACTIVITY") + ", " + c("rcp.c") + "; " + c("--inactivity-s"), "farewell 0x02; the desktop stays"],
        ["Session abandonment", "60 min", c("DEFAULT_ABANDON_MS") + ", " + c("main.c") + "; " + c("--abandon-s"),
         "the desktop is closed, with its programs; farewell 0x03 to anyone still watching"],
        ["QUIC idle timeout", "30 s", c("IDLE_MS") + ", " + c("transport.c"), "the transport's own, the same number as the silence clock"],
        ["Dead line", "5 s of stall, 10 s of silence", c("WT_LM_STALL_MS") + ", " + c("WT_LM_SILENCE_S") + ", " + c("webtransport.h"),
         "the connection is dropped; the stage stays"],
        "Handshake and login",
        ["Control channel to HELLO", "5 s", c("CAP_HELLO") + ", " + c("rcp.c"), "farewell 0x0D TIMED_OUT"],
        ["HERE_I_AM to CREDENTIALS", "60 s", c("CAP_CREDENTIALS"), "the same"],
        ["ADMITTED to ATTACH", "10 s", c("CAP_ATTACH"), "the same"],
        ["Fixed answer time", "1 s; refusal 2.5 s", c("FIXED_DELAY") + ", " + c("REJECT_FLOOR"), "an answer is never earlier"],
        ["Verdict ceiling", "12 s", c("VERDICT_CAP"), "no verdict is a no"],
        ["PAM request expiry", "8 s", c("EXPIRY_MS") + ", " + c("helper.c"), "a no, written in the log"],
        ["PAM check alarm", "20 s", c("GRANDCHILD_ALARM_S"), "the check kills itself"],
        ["Grant life", "30 s", c("RXR_GRANT_LIFE_MS") + ", " + c("rootside_proto.h"), "a grant not used for a SPAWN expires"],
        "Births and the stage",
        ["Wait for READY", "30 s", c("READY_WAIT_MS") + ", " + c("main.c"), "the network side exits"],
        ["Wait for SPAWNED", "15 s", c("SPAWN_WAIT_MS") + ", " + c("child.c"), "the login is refused"],
        ["Child introduction", "15 s", c("SHOW_UP_DEADLINE_MS"), "the child is killed"],
        ["Who-are-you", "every 60 s; 600 s to answer", c("RECHECK_MS") + ", " + c("WHOAMI_DEADLINE_MS"), "a stuck child is killed"],
        ["Wait for the client's canvas", "1.2 s", c("CANVAS_WAIT_MS"), "the stage starts at the fallback canvas"],
        ["Canvas answer to the client", "3 s", c("RCP_CANVAS_WAIT_MS") + ", " + c("rcp.h"), "NOT_NOW"],
        ["Stage retry", "200 ms, then 1 s doubling to 30 s", c("STAGE_BIRTH_RETRY_MS") + ", " + c("STAGE_RETRY_MIN_MS") + ", " + c("STAGE_RETRY_MAX_MS"),
         "how often a missing stage is asked for"],
        ["Session start wait", "40 s", c("WAIT_STARTUP_MS") + ", " + c("session.c"), "a blocking start gives up"],
        ["Closing grace", "30 s", c("CLOSING_GRACE_MS") + ", " + c("child.c"), "a child asked to close counts as alive again"],
        ["Input channel closed, life unknown", "3 rounds, 1 s apart", c("EIS_UNKNOWN_ROUNDS") + ", " + c("child.c"),
         "the compositor closed the input channel and the session's life is “unknown”: asked again before the child decides the session is over"],
        ["Close retry after a refused stage", "10 s", c("scale_close_ms") + ", " + c("child.c"), "a failed close of the session after a scale refusal is tried again"],
        ["Close-only life", "30 s", c("CLOSE_ONLY_LIFE_MS"), "the child leaves, desktop untouched"],
        "Local-login close on KDE (" + rif("Ending a graphical session") + ")",
        ["Orderly close before the forced one", "5 s", c("KDE_PRELOCAL_ORDERLY_MS") + ", " + c("session.c"), "only in the close made for a local login on KDE (it is " + c("WAIT_EXIT_MS") + ", 10 s, otherwise): "
         "then the forced stop of the graphical target; owner's decision of 25 Nov 2026. After it everything stopped in 0.54-0.56 s (PIANO.md)"],
        "Plasma logout rescue (" + rif("Ending a graphical session") + ")",
        ["Grace before the stop is repeated", "4 s", c("KDE_LOGOUT_GRACE_MS") + ", " + c("session.c"), "the normal end is given time to win"],
        ["Pause between attempts", "3 s", c("KDE_LOGOUT_RETRY_MS"), "the stop of the graphical target is asked again"],
        ["Attempts", "10 in mode “fail”, then 10 in mode “replace” (about a minute)", c("KDE_LOGOUT_TRIES"),
         "then the child closes the session by the product's own road, with the line “closing the graphical session by force”"],
        "Root side",
        ["Network side restart pause", "1 s doubling to 30 s; 60 s stable", c("NET_RESTART_FIRST_MS") + ", " + c("NET_RESTART_CAP_MS") + ", " + c("NET_STABLE_MS"),
         "how soon a dead network side is restarted"],
        ["Children after the network side dies", "5 s, then 3 s", c("KIDS_EOF_GRACE_MS") + ", " + c("KIDS_TERM_GRACE_MS"), "SIGTERM, then SIGKILL"],
        ["Network side stops", "25 s", c("STOP_WAIT_MS") + ", " + c("rootside.c"), "SIGKILL to the network side"],
        ["Desktops asked to close at a stop", "15 s", c("STOP_CLOSE_WAIT_MS") + ", " + c("main.c"),
         "what is still alive then is closed by the root side"],
        ["Desktops left in a REMOTIX scope", "scan every 5 s; SIGKILL 3 s after SIGTERM; clean-up up to 15 s",
         c("LX_EVERY_MS") + ", " + c("LX_TERM_MS") + ", " + c("LX_CLEAN_MS") + ", " + c("rootside.c"),
         "the root side ends a desktop with no child (seen in two scans in a row) and, at a stop, what is left"],
        ["Orphan close hold", "30 s per uid", c("ROOTSIDE_ORPHAN_UID_MS") + ", " + c("rootside.h"), "a second close for the same user is refused"],
        ["Sentinel", "1 s (asked twice) at attach, before a birth and before a logout; 300 ms periodic check; 2 s sweep",
         c("FAIL_CLOSED_WAIT_MS") + ", " + c("WAIT_MS") + ", " + c("LOCAL_SWEEP_MS") + " (" + c("ATTACH_WAIT_MS")
         + ", 100 ms, belongs to " + c("sentinel_local()") + ", no longer called)", "how long the loop may wait for logind"],
        "Local login hold (" + rif("The local-login hold") + ")",
        ["Child's full close before the root side acts", "13 s", c("PL_GRACE_MS") + ", " + c("rootside.c"),
         "the root side ends the scope itself"],
        ["Longest hold of a login by the root side", "20 s", c("PL_CEIL_MS"), "the request is removed and the login goes on, with a warning"],
        ["No birth after the answer", "10 s", c("PL_HOLD_MS"), "a new desktop for that uid is refused"],
        ["The hook's own ceiling", "25 s", c("LOCAL_CEIL_MS") + ", " + c("local_login.c"), "the hook gives up and exits 0"],
    ], "«TAB» — The clocks, each cited from its constant") + \
    p("<b>How the abandonment clock is fed.</b> By the five real input gestures of RCP §7.3 (pointer, button, wheel, letter, "
      "key by position), recorded by " + c("presence_mark()") + " per user in a table sized on the cap. Not by the release "
      "sent at detach (it arrives exactly when the user leaves), not by the canvas change that starts on its own at reattach, "
      "not by the request to log out. Resetting the clock at reattach was considered and discarded. " + c("abandon_round()")
      + " runs every pass of the loop, because an expiry that waits for an event never fires. If the root side finds a "
      "found-again desktop not yet abandoned by its own clock (which counts from its own start, or from the last child's exit) "
      "it refuses with " + c("RXR_REF_TOO_SOON") + " and the time to wait; the network side asks again, at most "
      + c("ABANDON_TOO_SOON_RETRIES") + " (3) times.") + \
    warn("The 30-minute and 60-minute clocks were verified only by mechanism at short values (" + c("prove/check-resilience.py")
         + ", check “clocks”: " + c("--inactivity-s 30") + " and " + c("--abandon-s 90") + ", then a new login is NEW). Their "
         "defaults are read from the startup line, not waited for, by design (owner's decision of 16 August 2026).",
         "Verified by mechanism.")

# ── Ending ──────────────────────────────────────────────────────────────
EXIT = seq([("Page", "browser", "light"), ("Network side", "user remotix", "navy"), ("Child", "the user", "blue"),
            ("Desktop", "compositor", "light")], [
    (3, 2, "the session ends (Log Out)", True),
    ("note", 2, "was alive, now dead"),
    (2, 1, "MSG_SESSION_FINISHED"),
    (1, 0, "FAREWELL 0x10 SESSION_TERMINATED"),
    ("note", 2, "clean up, SIGTERM self"),
    ("sep", "logind closes the session when its leader, the child, exits"),
], "«FIG» — Log Out from the desktop's own menu")

S8 = p("The user ends their session; the server ends it itself when it is abandoned, when the service stops, when a "
       "local login of the same user is held, and when no child holds it (the root side's rule “no orphan desktops”). "
       "Whatever the cause, the reason "
       "is sent to whoever is watching before the desktop dies (RCP.md §8.1, finding B-7: a silence would read as “network "
       "error”).", lead=True) + \
    table(["Cause", "Reason to the client", "How it ends"], [
        ["The user chooses Log Out in the desktop's menu", c("0x10 SESSION_TERMINATED"), "The child sees the session go from alive "
         "to dead (" + c("MSG_SESSION_FINISHED") + "), the network side sends the farewell at once, and the child ends its own "
         "process. On every desktop (17 Nov 2026) the logout ends the child, so the next login is a <b>new</b> session. On every desktop except KDE the "
         "farewell is sent <i>before</i> the stage is dismantled (" + rif("When the session ends before the stage is gone") + ")"],
        ["The page asks to end the session", c("0x10"), "The server handles " + c("TERMINATE_SESSION") + " (0x0011): the farewell "
         "goes out first, then the child is told with " + c("CHILDREN_INPUT_TERMINATE") + " and closes the session as below"],
        ["The abandonment clock expires", c("0x03 SESSION_ABANDONED"), c("abandon_expired()") + ": clients still attached are sent away, "
         "then the child (or a close-only child for a found-again desktop) closes the session"],
        ["The user has a local session", c("0x04 LOCAL_SESSION_PREVAILED") + " or " + c("0x05"), "The <i>light</i> close: only what is "
         "REMOTIX's is taken away (" + rif("Security model") + ")"],
        ["A local login of the user is held in PAM", c("0x04 LOCAL_SESSION_PREVAILED"), "The <i>full</i> close, because the local "
         "desktop has not started yet (" + rif("The local-login hold") + ")"],
        ["The service stops", c("0x0C SERVER_CLOSING"), "The full close (the light one for a user with a local session), "
         "then the root side ends what is left (" + rif("Stopping the service") + ")"],
    ], "«TAB» — How a graphical session ends") + EXIT + \
    p("<b>The close itself</b> (" + c("session_terminate()") + " in " + c("session.c") + ") asks the desktop's own manager to exit and "
      "waits " + c("WAIT_EXIT_MS") + " (10 s; 5 s for Plasma in the close made for a local login, " + c("KDE_PRELOCAL_ORDERLY_MS") + ") for the session to be gone, then forces: GNOME " + c("Logout(1)") + " then "
      + c("Logout(2)") + "; Plasma " + c("org.kde.Shutdown.logout") + " then a forced " + c("StopUnit(\"graphical-session.target\", \"fail\")") + " (REGISTRO F36: it used to stop "
      + sysf("plasma-workspace.target") + ", and KWin, ksmserver and plasmashell, which are part of the graphical target, went away only about 4.5 s later), with a rescue described "
      "below; XFCE "
      + c("org.xfce.Session.Manager.Logout") + " then SIGTERM to labwc; LXQt " + c("org.lxqt.session.logout") + " then the same. "
      "Then " + c("session_clear_out_scope()") + " removes what a desktop that detached itself left in the child's logind scope "
      "(SIGTERM, a pause, SIGKILL), and the user manager's variables and drop-ins carrying REMOTIX's mark are restored. If "
      "the close fails the log says the two truths do not match (the client has its farewell, the desktop is still there).") + \
    p("<b>Plasma: a logout that stops halfway</b> (" + c("session_kde_logout_watch()") + " in " + c("session.c") + ". It was written and measured on Kubuntu "
      "26.04 with Plasma 6.6 on 18 Nov 2026, REGISTRO D, an entry of the Ubuntu work; the code is the same here, but <b>that the rescue triggers on Plasma 6.8 has not been verified</b>; what "
      "is verified on Fedora is the forced close described above). “Log Out” starts " + c("plasma-shutdown") + ", which asks systemd to stop "
      + sysf("graphical-session.target") + " and exits without repeating the request. If a service (usually the portal) is still "
      "starting, systemd refuses, and the desktop stays up with the client never told. The older rescue waited for a unit to "
      "stop, which on Plasma 6.6 never happens. The rescue now notices that " + c("plasma-shutdown") + " has finished (it owns the "
      "bus name " + c("org.kde.Shutdown") + " while it runs), asks " + c("ksmserver") + " whether a logout is really in progress "
      "(" + c("isShuttingDown") + "), and only if the answer is yes waits " + c("KDE_LOGOUT_GRACE_MS") + " (4 s) and repeats the "
      "stop of the target every " + c("KDE_LOGOUT_RETRY_MS") + " (3 s): " + c("KDE_LOGOUT_TRIES") + " (10) times in mode “fail”, then "
      "as many in mode “replace”, which also passes a queued start job. If the stop is still refused after about a minute the "
      "function returns true and the child closes the session by the product's own road (log: “closing the graphical session by "
      "force”). If " + c("ksmserver") + " does not answer, or says no (a cancelled logout, an application asking to save), nothing "
      "is forced: unsaved work is worth more than a lost logout. Known limits: a power-off or reboot asked from the desktop does "
      "not release the bus name, so a refusal in the first seconds would stay lost (REMOTIX removes those menu entries); a restart "
      "of KWin during the wait resets the request.") + \
    p("<b>The light close</b> (" + c("local_light_close()") + ") is used when the user has a local session or logind could not "
      "say. Since 19 Nov 2026 the child sends " + c("MSG_LOCAL_FOUND") + " to the parent <i>before</i> it starts the close (the "
      "close dismantles the stage, which can wait for PipeWire), so the clients get their " + c("0x04") + " at once. The close "
      "dismounts the stage, releases the suspend inhibition, neutralises the session's dconf profile, closes what is "
      "left in the child's own seatless scope only if logind confirms it has no seat, stops REMOTIX's own KDE compositor "
      "service only if its processes carry REMOTIX's mark (" + c("--kwin-virtual") + " on the command line or " + c("REMOTIX_KDE_HOST=1") + " in the environment, " + c("kdehost.h")
      + "; a SELinux rule lets the root side stop and look at the units labelled " + c("xdm_unit_file_t") + ", REGISTRO F36), and restores the manager's marked variables. It never calls the "
      "session manager's logout, which is shared with the local desktop. Decisions: " + c("docs/DECISIONS-11.md") + ".") + \
    note("The page contains the confirmation dialog and " + c("run_logout()") + ", which sends " + c("TERMINATE_SESSION")
         + ", but nothing in " + c("page.html") + " opens the dialog: the " + c("Ctrl+Alt+End") + " shortcut that did was removed on "
         "17 August 2026. The message is served but has no way in from the page today. Log Out from the desktop's own menu is "
         "the only way for a user (SPECS §5.2-bis still describes the shortcut).", "TERMINATE_SESSION has no trigger.") + \
    p("<b>What was verified on Fedora.</b> " + c("prove/check-lifecycle.py") + " check 4 (“logout”) runs each desktop's own Log Out: the client is told, nothing of the "
      "user is left, and a new login gives a NEW session; " + c("login-after-other-logout") + " in " + c("prove/check-resilience.py") + " checks that a second user is untouched. These are part of "
      "the final round (PIANO.md, 23 Nov 2026; " + rif("What was verified and what was not") + "). The close made by a <i>local login</i> was proved by the owner by hand on a real machine on "
      "25 Nov 2026: GNOME, XFCE (orderly close in 1.7 s) and LXQt (0.7 s) passed; KDE failed with the package " + c("h1") + " and passed with " + c("i1") + " and " + c("i2")
      + " (forced at 5.04 s, everything stopped 0.56 s later, hook released at 5.9 s, no SELinux denial, no core dump). On KDE " + c("check-prelocal.py") + " (P1 to P8) and "
      + c("check-kde-exit.py") + " cover it on the bench. <b>Not tried:</b> the close by abandonment on KDE; programs that are slow to close on KDE, which the 5 s wait now cuts short (a healthy close "
      "that took between 5 and 10 s would be forced); XFCE ignores a Log Out asked while the desktop is still starting, which is the desktop's behaviour.") + \
    warn("Two limits are known and declared. (1) When the remote KDE session is closed “from outside” (the forced close) the background programs of Plasma abort with a core dump "
         "(" + c("kaccess") + ", " + c("kded6") + ", " + c("plasmashell") + " and others, 27 files in 25 s measured on the bench machine, REGISTRO F16): a normal Log Out leaves none. (2) GNOME has the same "
         "construction as KDE for a local-login close and <b>no last defence</b> if the orderly close does not end; the owner put this aside on 25 Nov 2026 (PIANO.md), and so the same "
         "forced-close code of Debian and Ubuntu, which is untouched.", "Declared limits of the close.")

# ── Ending early ────────────────────────────────────────────────────────
S8B = p("When a graphical session ends, the page must be told at once. The child therefore tells its parent <i>before</i> it dismantles its stage "
        "(capture, input, clipboard), so that the farewell does not wait for PipeWire, whose real-time module can sit in a D-Bus call to RealtimeKit for a long time on a "
        "machine where that service cannot start. That rule comes from the Ubuntu work (REGISTRO C5 and the history in " + c("docs/STORIA-ubuntu-26.04.md") + "), and the code is the same here. "
        "<b>The delays measured there are not repeated: they were not measured on Fedora.</b>", lead=True) + \
    p("<b>The rule</b> (" + c("session_over_early()") + " in " + c("child.c") + "). The child sends " + c("MSG_SESSION_FINISHED")
      + " to the parent first, and dismantles the stage afterwards. Four conditions hold together, and each exists because the "
      "farewell cannot be taken back:") + \
    table(["Condition", "Why"], [
        ["The session is <b>certainly</b> dead: " + c("session_life()") + " answered " + c("SESSION_LIFE_DEAD"),
         "“I could not look” is not death. In doubt nothing is said here, and the old road holds: the remount, a second later, asks "
         + c("session_state()") + " and decides"],
        ["The stage is not a KWin stage (" + c("stage_kwin") + " is false)", "KDE is left out: a KWin restarted by systemd leaves its "
         "bus name without an owner for a moment, so “no owner” is not certain there. On Fedora the KWin is " + c("--virtual") + " and not nested, and whether the exclusion is still "
         "needed has not been verified (no early farewell on Plasma)"],
        ["It was not said already (" + c("finished_told") + ") and the session was seen alive before (" + c("vista_viva") + ")",
         "once only; a desktop that was never seen alive cannot have ended"],
        ["The child is not a close-only child and the user did not close the session themselves", "those roads have their own farewell"],
    ], "«TAB» — When the farewell is sent early") + \
    table(["" + c("session_life()"), "Meaning", "What the child does"], [
        [c("SESSION_LIFE_ALIVE"), "the session bus answered and the name of the desktop's own service has an owner (Mutter's display service on GNOME, " + c("org.kde.KWin") + " on KDE, " + c("SESSION_BUS_XFCE") + " and " + c("SESSION_BUS_LXQT") + " for the session managers) and, on GNOME, " + c("GetCurrentState") + " answered", "nothing; the counter of unknown answers is reset"],
        [c("SESSION_LIFE_DEAD"), "the bus answered and that name has no owner", "the early farewell, then the dismantling"],
        [c("SESSION_LIFE_UNKNOWN"), "no bus, a call failed or timed out, any other error", "nothing is concluded; see below"],
    ], "«TAB» — The three answers about the life of the session") + \
    p("<b>Unknown is not dead.</b> At a logout the user's session bus itself goes away for a moment, so the answer can be "
      "“unknown” exactly when the session has just ended. When the compositor closes the input channel and the answer is unknown, "
      "the child asks again after one second, up to " + c("EIS_UNKNOWN_ROUNDS") + " (3) rounds, before it falls back to the old road "
      "(dismantle, no early farewell). The settings preparation at the child's start uses the same three answers (REGISTRO C5, 19 Nov "
      "2026): alive, it writes the session's runtime dconf profile at once; dead, it neutralises a file of ours left behind and "
      "writes at the birth; unknown, it touches nothing and the birth writes the file if it is missing. The branch “unknown” at the "
      "child's start was not exercised on a machine, on Ubuntu or on Fedora (REGISTRO C5).") + \
    p("<b>What the parent does.</b> It counts the child as <i>closing</i> from the moment it receives the message (" + c("closing_asked_ms")
      + ", for at most " + c("CLOSING_GRACE_MS") + ", 30 s). A login in the meantime is refused with the true " + c("0x0E")
      + " “still closing” and is never given a desktop that is going away (" + rif("From password to admission") + "). The clients that "
      "were logged in get " + c("0x10") + " at once through " + c("wt_dismiss_user_session_over()") + " (" + rif("From password to admission")
      + "). After the early message the child cannot find the session again in any branch of its loop except one: a compositor that takes "
      "its name back before the remount reads it (about a second; nothing of REMOTIX does that, and the Shell's unit is not restarted). "
      "Otherwise the remount reads “dead” with the session seen alive, takes the §7.6 road, and ends the child with " + c("SIGTERM")
      + ". In that one case the clients are already gone and the parent keeps the child “closing” for the grace period.") + \
    p("<b>The stage refused for the scale.</b> If the user has a screen scale other than 1 (their own settings, or Settings → "
      "Displays saved in " + sysf("monitors.xml") + ") the pointer would go elsewhere, and guard 2 (DECISIONS §5.0-sexies) refuses to "
      "serve it. Since 19 Nov 2026 the child first makes <b>one temporary attempt</b> to bring its own monitor back to 1 "
      "(" + c("mutter_scale_to_one()") + ": nothing persistent, the user's files untouched). If the scale re-read is 1 the stage goes "
      "on. If not, " + c("MSG_STAGE") + " goes to the parent with " + c("fatal") + " set, the clients get " + c("0x0E") + " (" + c("stage_refused_by_child()")
      + " in " + c("main.c") + ") instead of a black page, and the child closes the graphical session by the road of the user's Logout "
      "(the check for a local session first, which turns it into the light close), retried every 10 s if it fails; once the session "
      "is gone the child leaves, so nothing stays alive. The cause upstream is cured in the session's dconf rules, where "
      + c("scaling-factor") + " is locked to 1 (a key of the table " + c("DCONF_KEYS") + " added on 19 Nov 2026, with the user's own "
      "file never touched); the refusal is the net under it, and its log line lists the likely causes: a scale saved from Settings, a mandatory dconf "
      "profile of the administrator, or the fallback without " + c("dconf compile") + ", where the lock does not hold. On KDE the second refusal is the one for a KWin without "
      + c("kde_output_management_v2") + ": it takes the same road (" + c("fatal") + ", " + c("scale_refused") + "), REGISTRO F13 (" + rif("KDE: KWin alone") + ").") + \
    note("The early farewell and the Plasma rescue have the same origin, a window in which the desktop is over and the clients "
         "do not know: the first closes it on every desktop but KDE, the second (" + rif("Ending a graphical session") + ") on Plasma. "
         "The records are in the comments of " + c("session_over_early()") + " and " + c("session_kde_logout_watch()") + ", and in "
         + c("docs/REGISTRO-problemi.md") + " (D).", "Same window, two cures.")

# ── Shutdown ────────────────────────────────────────────────────────────
S9 = p("When systemd stops the unit (" + c("systemctl stop") + " or " + c("restart") + ", a package upgrade that restarts the "
       "service, a shutdown), <b>every remote desktop is closed</b>, as at a reboot. Until 17 Nov 2026 the desktops stayed "
       "for the new service to find; the owner's decision of that night (" + c("DECISIONS-11") + " §11.56) reversed it, "
       "because a desktop left without anyone to watch it breaks the local login of the same user (" + rif("The local-login hold")
       + ").", lead=True) + steps([
        "<b>Signal.</b> SIGTERM reaches the root side, which sends SIGTERM to the network side and waits " + c("STOP_WAIT_MS")
        + " (25 s, " + c("rootside.c") + ") for it and for the children; the log says “the network side is asked to stop (SIGTERM), 25 s at most”.",
        "<b>Farewell.</b> The network side leaves its loop and calls " + c("transport_dismiss_all()") + " with " + c("RCP_SERVER_CLOSING")
        + " (0x0C), “the server is shutting down”, polling the socket for at most 4000 ms until every session is closed, then 50 "
        "more rounds of 10 ms so that the closing capsule really leaves; if some sessions did not finish it says so.",
        "<b>The desktops are asked to close.</b> For every child that is alive the network side sends the request to close its "
        "desktop and waits at most " + c("STOP_CLOSE_WAIT_MS") + " (15 s, " + c("main.c") + "). A user with no local session gets the full "
        "close (the desktop's own logout); a user who has a local session, or for whom logind could not be asked, gets the "
        "<i>light</i> close, never the session manager's logout (the log says “its desktop gets the LIGHT close, not the "
        "Logout”). Desktops found again that have no child here are left to the root side. If the root side is already gone "
        "no request is sent: the children see the end-of-file and leave, and the next root side ends the desktops.",
        "<b>Tidy.</b> " + c("helper_turn_off()") + ", " + c("sentinel_close()") + ", " + c("page_close()") + ", " + c("transport_close()")
        + ", then " + c("children_turn_off()") + ": each child's socket is closed (the end-of-file is the second net, "
        "beside " + c("PR_SET_PDEATHSIG") + "), the child gets SIGTERM and " + c("TURN_OFF_WAIT_MS") + " (1500 ms) to be reported "
        "gone by the root side. A child on SIGTERM dismounts its stage (capture, virtual monitor) and exits.",
        "<b>The root side ends what is left.</b> Once the network side is gone (or at the deadline) the root side ends whatever "
        "is still in a REMOTIX scope: SIGTERM to that scope's processes, SIGKILL " + c("LX_TERM_MS") + " (3 s) later, the clean-up "
        "of what REMOTIX put in the user manager (up to " + c("LX_CLEAN_MS") + ", 15 s), all bounded by the root side itself; it "
        "waits for these endings (21 s at most) before it exits. If nothing was left at its scan it says “⭐ no orphan desktops: no REMOTIX "
        "session is left with processes — the service stops clean”; if it had to end something, the lines are the per-session “⛔ no orphan "
        "desktops: the REMOTIX session N of «user» (uid N) is still there while the service stops — it must not stay: SIGTERM …”; if something is "
        "still there at the ceiling it says “⛔ no orphan desktops: the service stops and N REMOTIX session(s) still have processes (…): the "
        "next start of the service ends them”. " + c("KillMode=mixed") + " takes anything left of the unit.",
    ]) + \
    p("The stop takes a few seconds when the desktops close by themselves. The code states these bounds and no other total: "
      "25 s for the network side and the children, 15 s of those for the close of the desktops, and the root side's own endings "
      "after that (SIGTERM, SIGKILL after 3 s, clean-up up to 15 s). A user with a client open is sent away with 0x0C; a new login "
      "gives a NEW session, and the programs of the old desktop, with their unsaved work, are gone. In the journal, area "
      + c("startup") + ", the lines are “stopping: N desktops asked to close (waiting at most 15 s for them)” and “stopping: N desktops "
      "closed, M still alive after 15 s”; a request that did not leave says “the request to close the desktop of … did NOT leave "
      "towards its child”. Area " + c("rootside") + " has the “no orphan desktops” lines.") + \
    p("A restart of the network side alone (a crash, or the root side's decision after a malformed packet) closes the clients' "
      "connections without a farewell, since the process is gone; the root side then restarts it. The children see the "
      "end-of-file, and a desktop left without a child is listed as found again for the new network side and ended by the root "
      "side within about 10 s, unless its user logs in first (" + rif("Desktops found again after a restart") + "). "
      "After a restart of the whole service, " + c("prove/check-resilience.py") + " (“service-restart”) checks that the client is "
      "told or returns to the form (within 45 s), that no REMOTIX session of the user and no process of the old window are left, "
      "that the root side's journal says “the service stops clean”, and that a new login is a NEW session with a working "
      "desktop.") + \
    tip("Restarting the unit to install a new package closes the remote desktops: " + c("%systemd_postun_with_restart") + " restarts the "
        "service if it was running, and the restart is a stop followed by a start. At removal " + c("%preun") + " closes the sessions first (only on removal, "
        "<code>$1 = 0</code>, never on an upgrade), stops the service, takes the PAM hook out, and only then the user's " + sysf("graphical-session.target") + " if the user has no other graphical "
        "session; on an upgrade the stop closes them all the same. Warn the users of a busy server before upgrading; they log in again and get a new session. "
        "The package installs " + sysf("/etc/needrestart/conf.d/remotix.conf") + " (" + c("rpm/needrestart.conf") + "), which sets " + c("$nrconf{override_rc}{qr(^remotix\\.service$)} = 0")
        + ": if " + c("needrestart") + " is used on the machine it does not restart the service by itself after an update of a library it uses (libc, OpenSSL, PAM), which would close "
        "every remote desktop; the service is only listed under “Services to be restarted manually”. <b>Fedora does not ship " + c("needrestart") + " by default</b>; whether it is in "
        "the repositories and whether " + c("dnf-automatic") + " uses it has not been verified, so the file is a precaution and nothing more.",
        "Upgrades close the desktops.")

# ── Log lines ───────────────────────────────────────────────────────────
S10 = p("A defect in this chain rarely names its cause: the user sees “black”, “slow” or “nothing happens”. The log line "
        "that marks each step is the map. The first token after the time is the area (" + c("rootside") + ", " + c("child") + ", "
        + c("session") + ", " + c("startup") + "…); the log chapter has the format (" + rif("Logging and diagnostics") + ").",
        lead=True) + \
    table(["Step", "Area", "The line contains"], [
        ["Service up", "rootside", "“ROOT SIDE on”, “network side started”, “the network side's walls in force”, and for SELinux “SELinux: born in system_u:system_r:remotix_net_t:s0” "
         "(or “⚠ SELinux: on, but the root side is not in remotix_t”)"],
        ["Hook of the local login", "the unit's journal", "the line of " + c("remotix-pam-hook check") + " that the " + c("ExecStartPre") + " writes at every start"],
        ["Card probe", "startup", "“video.codec offered”, or “THIS SERVER CANNOT ENCODE VIDEO”"],
        ["Ready", "startup", "“ready: https://…”"],
        ["Clocks and cap", "startup", "“the three clocks in force”, “ADMINISTRATIVE session cap”"],
        ["Found again", "child", "“FOUND AGAIN the desktop of”, “live REMOTIX desktops found again at startup”"],
        ["A password refused before PAM", "rootside", "“AUTH refused BEFORE PAM”, “not asked of PAM”"],
        ["Birth", "rootside, child", "“the birth for … took N ms”, “I am the child of”"],
        ["No stage", "child", "“NO STAGE at birth”, “loop ALIVE without a stage”"],
        ["Detach", "rcp", "“DETACHED for silence”, “INACTIVITY”"],
        ["Come back", "child", "“COMES BACK to their desktop found again”"],
        ["Log Out", "child", "“§7.6”, “the graphical session WAS THERE and now is NO LONGER”"],
        ["Abandonment", "startup, child", "“§5.3 — ABANDONMENT”, “the session is ABANDONED”"],
        ["Local session", "child", "“defence 1”, “defence 2”, “defence 3”, “light close”"],
        ["Shutdown", "startup", "“shutdown requested”, “farewell 0x0c sent to all sessions”"],
        ["Stop: desktops closed", "startup, rootside", "“stopping: N desktops asked to close”, “N desktops closed, M still alive after 15 s”, "
         "“no orphan desktops: no REMOTIX session is left with processes”"],
        ["Orphan desktop ended", "rootside", "“no orphan desktops: the REMOTIX session N of … has live processes and no child of ours”"],
        ["Local login hold", "rootside", "“local login of … HELD in PAM”, “nothing of its REMOTIX desktop is left”, "
         "“STILL there after 20 s” (the other lines are in " + rif("Logging and diagnostics") + ")"],
        ["GNOME session chosen", "session", "“D8: the GNOME session is «gnome»” on Fedora with the candidates and the start line; “D8: no wayland-sessions/*.desktop session launches gnome-session…: DECLARED FALLBACK”"],
        ["Settings fallback", "session", "“DECLARED FALLBACK, D-015 (19 Nov 2026)”: the session runs without the system dconf database"],
        ["Desktop cannot be born", "child, session", "“passed PAM but the desktop cannot be born: … needs `labwc` and it is NOT installed”; at startup “labwc is NOT there, and XFCE/LXQt cannot start”"],
        ["Session over, told early", "child", "“the graphical session of «user» is over, CERTAINLY (…): the parent is told NOW, before the stage is dismantled”"],
        ["Plasma logout rescue", "session, child", "“Plasma logout stopped halfway: stop of graphical-session.target accepted / refused (attempt N, mode …)”; “closing the graphical session by force”"],
        ["A KDE session refused, or the declared fallback", "child", "“⛔ KDE: SESSION REFUSED, and closed — …”; “⚠ KDE: KWin's output did not reach WxH … DECLARED FALLBACK”"],
        ["SELinux refusal of a login", "child", "the messages of the exit codes 44 to 47: “⛔ SELinux: no context like a local login's could be worked out for the user: the login is REFUSED”, "
         "“the exec context could not be set”, “the next exec would not leave the root side's domain”, “the session keyring could not be made with the user's context”"],
        ["A connection closed", "transport", "“connection with … closed (n left)” followed by the reason (" + rif("Why a connection closed") + ")"],
        ["Stage refused for the scale", "child, wt", "“the user's scale … is NOT served: I try ONCE to bring our monitor back to 1”; “the stage was refused for the scale: the graphical session is closed”"],
    ], "«TAB» — The log line that marks each step") + \
    p("The priority marks of the journal (a leading ⛔ is an error, a leading ⚠ a warning, anything else information) were "
      "reviewed on 17 November 2026: of 33 message patterns seen at error priority, 29 routine ones were lowered to "
      "information or warning and 4 were kept as errors (" + c("docs/REGISTRO-priorita.md") + ").")

CHAPTER = ("Startup and life cycle", [
    ("Service startup, step by step", S1),
    ("The card that arrives late", S1B),
    ("The systemd unit and its life-cycle settings", S2),
    ("From password to admission", S3),
    ("Birth of a graphical session", S4),
    ("KDE: KWin alone", KDE),
    ("Detach and reattach", S5),
    ("Desktops found again after a restart", S6),
    ("The clocks, each one cited from its constant", S7),
    ("Ending a graphical session", S8),
    ("When the session ends before the stage is gone", S8B),
    ("Stopping the service", S9),
    ("The log line that marks each step", S10),
])
