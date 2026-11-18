from build import arrow, box, c, fig, note, p, path, rif, seq, steps, sysf, table, text, tip, warn, zone

# ── Service start ────────────────────────────────────────────────────────
S1 = p("The service starts in two stages: the root side (" + rif("The root side") + ") does its own work and forks the "
       "network side, and the network side then runs the rest of " + c("main()") + ". Both write at startup what the "
       "machine can do and which values are in force, so that a missing piece is read in the log rather than discovered by "
       "the first user.", lead=True) + \
    p("<b>In the root side</b>, before the network side exists: the options are parsed; the network user is resolved once, "
      "as root (" + c("getpwnam()") + " of " + c("remotix") + "; if it is missing or is uid 0 the service exits with "
      + c("EXIT_CONFIG") + " = 78, which the unit's " + c("RestartPreventExitStatus=78") + " does not retry); the certificate "
      "folder, the ban file and the page must lie where the network side can use them (inside " + c("--network-state-dir")
      + ", and the page readable by " + c("remotix") + "), or the service also exits with 78 and says which option to fix; the "
      "UDP and TCP port are bound; then " + c("rootside_main()") + " probes the card, sweeps the card ACLs of a previous run, "
      "starts the PAM dispatcher and the network side.") + \
    p("<b>In the network side</b>, in the order of " + c("main()") + ":") + steps([
        "<b>Born right.</b> " + c("network_side_born_right()") + " (" + rif("The network side and its walls") + "), then "
        + c("rootside_attach()") + " waits up to " + c("READY_WAIT_MS") + " (30 s) for " + c("RXR_READY") + ".",
        "<b>What is offered to the browser.</b> The codecs of the " + c("HERE_I_AM") + " are not measured here: " + c("READY")
        + " carries the root side's probe (" + c("child_video_capabilities()") + "). A machine with no card that encodes "
        "logs why, and every " + c("HELLO") + " ends in " + c("NOTHING_IN_COMMON") + " until a codec appears "
        "(" + rif("The card that arrives late") + ").",
        "<b>The desktop.</b> " + c("session_desktop_explain()") + " says which desktop this machine will start and why; on KDE "
        + c("kwin_check_permission()") + " checks that the " + c(".desktop") + " file that lets KWin offer screen capture to "
        "this binary is there (the package ships " + c("debian/org.kde.remotix.desktop") + ").",
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
        ["A probe finds codecs", "It sends " + c("RXR_CODEC") + " (" + c("offered") + " and " + c("explanation") + "); the "
         "network side's hook " + c("codec_from_root()") + " sets " + c("video.codec") + " for the next " + c("HERE_I_AM")
         + ". A network side started afterwards gets the result in " + c("READY") + "; the network side also asks "
         "again when a " + c("HELLO") + " finds the list empty (" + c("rcp_video_codec_retry_hook()") + ")"],
    ], "«TAB» — A card that arrives after startup") + \
    p("On a machine with no card at all the package refuses a <i>new</i> installation (PIANO.md, 17 Nov 2026, 19:40; "
      + rif("The package") + "), so this case matters for a card that is present but late, or for an upgrade.")

# ── Unit ────────────────────────────────────────────────────────────────
S2 = p("The service is the system unit " + c("debian/remotix.service") + ", installed by " + c("dh_installsystemd") + " with " + c("--no-enable --no-start") + " (" + c("debian/rules") + "): the package "
       "puts the unit there but the administrator enables and starts it, and an upgrade restarts it only if it was already "
       "running (the postinst's debhelper part does a try-restart). The settings that shape the life cycle:", lead=True) + \
    table(["Setting", "Value", "Why"], [
        [c("Type"), c("simple"), "the root side is the main process; " + c("exec") + " in the " + c("ExecStart") + " shell keeps it so"],
        [c("After="), c("network.target") + " and " + sysf("systemd-logind.service"), "logind must be there for sessions and for the sentinel"],
        [c("KillMode"), c("mixed"), "SIGTERM to the root side only, then SIGKILL to what is left of the unit; the desktops "
         "are outside the unit (" + c("setsid --fork") + ") and survive a stop"],
        [c("Restart"), c("on-failure") + ", " + c("RestartSec=2"), "a crash restarts the root side, which finds the desktops again"],
        [c("RestartPreventExitStatus"), c("78"), "a configuration error (" + c("EXIT_CONFIG") + ") is not retried"],
        [c("LimitRTPRIO"), c("20"), "priority for audio and video threads"],
        [c("LimitNICE"), c("-11"), "the same"],
        [c("User="), "not set", "the unit runs as root; hardening is in the program (" + rif("The network side and its walls") + ")"],
        [c("EnvironmentFile"), c("/usr/share/remotix/remotix.conf") + " then " + c("/etc/remotix/remotix.conf.d/*.conf"),
         c("REMOTIX_PORT") + " (7447) and " + c("REMOTIX_OPTIONS") + " (empty); the last " + c("--name") + " wins"],
    ], "«TAB» — The unit's settings that matter for the life cycle") + \
    warn("The comments at the top of the unit are partly stale: they say the package does not enable the unit “the engine "
         "does” (there is no engine in this tree), and they mention a " + c("--without split") + " build that no longer "
         "exists. The settings in the table are those in force.", "Old comments in the unit.")

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
        "stages of the server all in use (" + c("stage_count()") + " not below " + c("rcp_cap()") + ", " + c("0x0E") + "); "
        "the budget (" + c("has_capabilities()") + ", " + c("0x06 BUDGET_FULL") + "); then the birth.",
        "<b>The birth.</b> " + c("children_ensure_from()") + " sends " + c("RXR_SPAWN") + " with the grant and waits up to "
        + c("SPAWN_WAIT_MS") + " (15 s: at a user's first login the birth includes " + c("usermod") + ", itself bounded to "
        "5 s). The root side checks the grant, the name, that no child of that uid exists, the cap, and that the canvas "
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
    tip("None of the admission checks forks a process: a user refused for a local session, a full cap or the budget costs no "
        "child. One case is not closed completely: a desktop found again of a user who then opens a local session is left "
        "alone and removed from the list, because only the root side may end a logind session and the closed list has no "
        "message for it (" + c("found_again_close_for_local()") + " says so in the log; Appendix C).",
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
        "the desktop is detached from the child's process group, which is why it survives the child, the service and a "
        "restart. Its output goes to " + c("~/.local/state/remotix/session.log") + " (the user's state folder). The start "
        "command is the desktop's own: " + c("gnome-session") + " with the Shell's unit overridden to start headless, "
        + c("startplasma-wayland") + ", " + c("xfce4-session") + " on a labwc, or " + c("lxqt-session") + " on a labwc "
        "(" + rif("The four desktops") + ").",
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
      "wayland, class user, no seat) and carries the session's reference fifo across the " + c("execve()")
      + ". The logind session therefore lives as long as the child; a desktop's processes are in that session's scope. "
      "A session without a seat is headless, which on GNOME is the only form in which the screen locker does not revoke the "
      "capture (" + c("sentinel_without_seat()") + " verifies it after startup). " + rif("The per-user child")
      + " has the details of the fork.") + \
    note("On Debian 13 the unit file of the GNOME Shell is " + sysf("org.gnome.Shell@wayland.service") + " (" + c("SESSION_UNIT_SHELL_48")
         + " in " + c("session.h") + "); the drop-in that removes the monitors of its own is written at every birth and "
         "verified, because a line that can be lost is not a protection (invariant I7).", "GNOME 48.")

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
S6 = p("Stopping or crashing the service does not stop the desktops. The service, the PAM dispatcher and the children die; "
       "each desktop, started with " + c("setsid --fork") + " outside the unit, lives on with its programs (measured on 29 "
       "September 2026, ten runs out of ten on the four desktops, and re-verified for the restart on 17 November: "
       + c("prove/check-resilience.py") + ", “service-restart”). A new service must therefore find them, or nobody counts "
       "them, and the first new user could have them knocked down.", lead=True) + \
    p("<b>The criterion</b> (" + c("rediscover.h") + "), the same for all desktops: a logind session with " + c("Service=remotix")
      + ", in any state (it is “closing” as soon as the child that held the session's fifo is gone, which is the case after "
      "a stop of the service; the comment in " + c("rediscover.h") + " still describes the behaviour before 17 November "
      "2026, when it was “closing” a moment after birth), that contains a process of the user which is leader of its own process session (pid equals sid) and whose "
      "parent is not in the same scope. That is the signature of " + c("setsid --fork") + ": " + c("gnome-session-binary")
      + ", " + c("startplasma-wayland") + " or " + c("labwc") + ". A terminal opened inside the desktop does not match, because "
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
         "(" + c("RXR_CLOSE_ORPHAN") + ", no password) to close it (" + rif("Ending a graphical session") + ")"],
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
        ["Close-only life", "30 s", c("CLOSE_ONLY_LIFE_MS"), "the child leaves, desktop untouched"],
        "Root side",
        ["Network side restart pause", "1 s doubling to 30 s; 60 s stable", c("NET_RESTART_FIRST_MS") + ", " + c("NET_RESTART_CAP_MS") + ", " + c("NET_STABLE_MS"),
         "how soon a dead network side is restarted"],
        ["Children after the network side dies", "5 s, then 3 s", c("KIDS_EOF_GRACE_MS") + ", " + c("KIDS_TERM_GRACE_MS"), "SIGTERM, then SIGKILL"],
        ["Network side stops", "5 s", c("STOP_WAIT_MS"), "SIGKILL"],
        ["Orphan close hold", "30 s per uid", c("ROOTSIDE_ORPHAN_UID_MS") + ", " + c("rootside.h"), "a second close for the same user is refused"],
        ["Sentinel", "1 s (asked twice) at attach, before a birth and before a logout; 300 ms periodic check; 2 s sweep",
         c("FAIL_CLOSED_WAIT_MS") + ", " + c("WAIT_MS") + ", " + c("LOCAL_SWEEP_MS") + " (" + c("ATTACH_WAIT_MS")
         + ", 100 ms, belongs to " + c("sentinel_local()") + ", no longer called)", "how long the loop may wait for logind"],
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
    ("sep", "logind closes the session when the child's fifo closes"),
], "«FIG» — Log Out from the desktop's own menu")

S8 = p("Only the user ends their session, and the server ends it itself only when it is abandoned. Whatever the cause, the reason "
       "is sent to whoever is watching before the desktop dies (RCP.md §8.1, finding B-7: a silence would read as “network "
       "error”).", lead=True) + \
    table(["Cause", "Reason to the client", "How it ends"], [
        ["The user chooses Log Out in the desktop's menu", c("0x10 SESSION_TERMINATED"), "The child sees the session go from alive "
         "to dead (" + c("MSG_SESSION_FINISHED") + "), the network side sends the farewell at once, and the child ends its own "
         "process. On every desktop (17 Nov 2026) the logout ends the child, so the next login is a <b>new</b> session"],
        ["The page asks to end the session", c("0x10"), "The server handles " + c("TERMINATE_SESSION") + " (0x0011): the farewell "
         "goes out first, then the child is told with " + c("CHILDREN_INPUT_TERMINATE") + " and closes the session as below"],
        ["The abandonment clock expires", c("0x03 SESSION_ABANDONED"), c("abandon_expired()") + ": clients still attached are sent away, "
         "then the child (or a close-only child for a found-again desktop) closes the session"],
        ["The user has a local session", c("0x04 LOCAL_SESSION_PREVAILED") + " or " + c("0x05"), "The <i>light</i> close: only what is "
         "REMOTIX's is taken away (" + rif("Security model") + ")"],
    ], "«TAB» — How a graphical session ends") + EXIT + \
    p("<b>The close itself</b> (" + c("session_terminate()") + " in " + c("session.c") + ") asks the desktop's own manager to exit and "
      "waits " + c("WAIT_EXIT_MS") + " (10 s) for the session to be gone, then forces: GNOME " + c("Logout(1)") + " then "
      + c("Logout(2)") + "; Plasma " + c("org.kde.Shutdown.logout") + " then a forced stop of the unit; XFCE "
      + c("org.xfce.Session.Manager.Logout") + " then SIGTERM to labwc; LXQt " + c("org.lxqt.session.logout") + " then the same. "
      "Then " + c("session_clear_out_scope()") + " removes what a desktop that detached itself left in the child's logind scope "
      "(SIGTERM, a pause, SIGKILL), and the user manager's variables and drop-ins carrying REMOTIX's mark are restored. If "
      "the close fails the log says the two truths do not match (the client has its farewell, the desktop is still there).") + \
    p("<b>The light close</b> (" + c("local_light_close()") + ") is used when the user has a local session or logind could not "
      "say: it dismounts the stage, releases the suspend inhibition, neutralises the session's dconf profile, closes what is "
      "left in the child's own seatless scope only if logind confirms it has no seat, stops REMOTIX's own KDE compositor "
      "service only if its processes carry REMOTIX's mark, and restores the manager's marked variables. It never calls the "
      "session manager's logout, which is shared with the local desktop. Decisions: " + c("docs/DECISIONS-11.md") + ".") + \
    note("The page contains the confirmation dialog and " + c("run_logout()") + ", which sends " + c("TERMINATE_SESSION")
         + ", but nothing in " + c("page.html") + " opens the dialog: the " + c("Ctrl+Alt+End") + " shortcut that did was removed on "
         "17 August 2026. The message is served but has no way in from the page today. Log Out from the desktop's own menu is "
         "the only way for a user (SPECS §5.2-bis still describes the shortcut).", "TERMINATE_SESSION has no trigger.") + \
    p("<b>What was verified.</b> " + c("prove/check-lifecycle.py") + " check 4 (“logout”) runs each desktop's own Log Out "
      "(" + c("xfce4-session-logout --logout") + ", the LXQt and GNOME and KDE D-Bus calls): the client is told, nothing of the "
      "user is left in the box, and a new login gives a NEW session. " + c("login-after-other-logout") + " in "
      + c("prove/check-resilience.py") + " checks that a second user is untouched. Two corrections of 17 November 2026 are "
      "recorded in PIANO.md: the logind session now lasts for the whole life of the desktop and Log Out really closes it on "
      "all four desktops (" + c("child.c") + "), and on KDE a Log Out succeeds even if systemd refuses the stop (" + c("session.c")
      + "). XFCE ignores a Log Out asked while the desktop is still starting; that is the desktop's behaviour.")

# ── Shutdown ────────────────────────────────────────────────────────────
S9 = p("When systemd stops the unit, the root side asks the network side to stop; the network side says goodbye to every client "
       "before it closes QUIC, then lets its children go; the desktops stay.", lead=True) + steps([
        "<b>Signal.</b> SIGTERM reaches the root side, which sends SIGTERM to the network side and waits " + c("STOP_WAIT_MS")
        + " (5 s).",
        "<b>Farewell.</b> The network side leaves its loop and calls " + c("transport_dismiss_all()") + " with " + c("RCP_SERVER_CLOSING")
        + " (0x0C), “the server is shutting down”, polling the socket for at most 4000 ms until every session is closed, then 50 "
        "more rounds of 10 ms so that the closing capsule really leaves; if some sessions did not finish it says so.",
        "<b>Tidy.</b> " + c("helper_turn_off()") + ", " + c("sentinel_close()") + ", " + c("page_close()") + ", " + c("transport_close()")
        + ", then " + c("children_turn_off()") + ": each child's socket is closed (the end-of-file is the second net, "
        "beside " + c("PR_SET_PDEATHSIG") + "), the child gets SIGTERM and " + c("TURN_OFF_WAIT_MS") + " (1500 ms) to be reported "
        "gone by the root side. A child on SIGTERM dismounts its stage (capture, virtual monitor) and exits; its desktop "
        "stays, unless the user had logged out.",
        "<b>The root side</b> reaps the children, waits at most the same deadline for stragglers, and exits with 0; "
        + c("KillMode=mixed") + " takes anything left.",
    ]) + \
    p("A restart of the network side alone (a crash, or the root side's decision after a malformed packet) closes the clients' "
      "connections without a farewell, since the process is gone; the root side then restarts it and the desktops are found "
      "again. After a restart of the whole service, " + c("prove/check-resilience.py") + " (“service-restart”) verified that the "
      "page is told or returns to the form, and that a new login says RESUMED with the same window, text and working input.") + \
    tip("Restarting the unit to install a new package is safe for the users: the postinst's debhelper part does a try-restart, "
        "so the service restarts only if it was running, and the desktops stay. A user with a client open must log in again.",
        "Upgrades keep the desktops.")

# ── Log lines ───────────────────────────────────────────────────────────
S10 = p("A defect in this chain rarely names its cause: the user sees “black”, “slow” or “nothing happens”. The log line "
        "that marks each step is the map. The first token after the time is the area (" + c("rootside") + ", " + c("child") + ", "
        + c("session") + ", " + c("startup") + "…); the log chapter has the format (" + rif("Logging and diagnostics") + ").",
        lead=True) + \
    table(["Step", "Area", "The line contains"], [
        ["Service up", "rootside", "“ROOT SIDE on”, “network side started”, “the network side's walls in force”"],
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
    ("Detach and reattach", S5),
    ("Desktops found again after a restart", S6),
    ("The clocks, each one cited from its constant", S7),
    ("Ending a graphical session", S8),
    ("Stopping the service", S9),
    ("The log line that marks each step", S10),
])
