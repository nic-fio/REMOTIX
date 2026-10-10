from build import arrow, box, c, code, fig, note, p, path, rif, seq, steps, table, text, tip, warn

S1 = p("The server starts from " + c("main()") + " in " + c("main.c") + ". Before opening a port it finds out what "
       "the machine can do and writes it in the log, so that a missing piece is read at startup rather than "
       "discovered by the first user.", lead=True) + steps([
    "<b>Role.</b> With " + c("--figlio-interno") + " as first argument the process is a child and goes to "
    + c("figlio_vive()") + "; with " + c("--prova-codifica") + " (encoding test) it encodes one frame on the GPU, prints one JSON "
    "line and exits (0 the GPU encodes, 1 it opens but no frame comes out, 2 usage error, 3 no GPU can encode).",
    "<b>Options.</b> The command line is read; an unknown option prints the usage and exits with 2. Options that "
    "no longer exist (" + c("--ritmo-adattivo") + ", " + c("--linea-morta") + ", " + c("--sblocca") + " — adaptive pace, "
    "dead line, unblock) exit with "
    "2 and a sentence saying what replaced them, instead of being silently ignored. Without a real "
    + c("--nome") + " (the name; empty, " + c("0.0.0.0") + " or " + c("::") + ") the server refuses to start: the "
    "certificate must carry the name the browser will use.",
    "<b>Signals.</b> " + c("SIGINT") + " and " + c("SIGTERM") + " only set a flag that ends the loop; "
    + c("SIGPIPE") + " is ignored. With " + c("--journal") + " every log line also goes to the systemd journal ("
    + rif("Logging and diagnostics") + ").",
    "<b>The GPU.</b> A forked process opens each encoder on a 256×256 frame (" + c("figlio_capacita_video()")
    + "); its answer, or its silence after 30 s, decides the codecs that the " + c("ECCOMI") + " will offer. In a "
    "separate process because a driver that crashes must not take the server down before it has a port. With no "
    "GPU that encodes, the log says so with the reason for each codec and every " + c("CIAO") + " (the client's "
    "hello) will end in " + c("NIENTE_IN_COMUNE") + " (nothing in common).",
    "<b>The desktop.</b> " + c("sessione_desktop()") + " recognises the desktop from the programs in the "
    + c("PATH") + " and the log says which, and why; on KDE " + c("kwin_verifica_permesso()") + " checks that the "
    + c(".desktop") + " file that lets KWin offer screen capture to this binary is in place.",
    "<b>Clocks and switches.</b> The three session clocks, the five network cures of phase 9, the session cap "
    "and the budget are written in the log with the value in force, on <i>and</i> off (I6): a one-hour clock "
    "cannot be checked by waiting an hour.",
    "<b>The ban.</b> " + c("rcp_ban_carica()") + " reads " + c("/var/lib/remotix/ban") + "; if the file cannot "
    "be read the server exits with 1 rather than forget who was banned.",
    "<b>The PAM helper</b> (" + c("aiutante_accendi()") + "), before any port is open, so that it does not inherit "
    "them. If it does not start, the server goes on and every login will be refused — and the log says so.",
    "<b>The children table</b> (" + c("figli_accendi()") + "), sized on the session cap; it resolves "
    + c("/proc/self/exe") + " once, for the children's " + c("execve") + ".",
    "<b>The unblock socket</b> (" + c("comando_apri()") + "), only with " + c("--comando-socket") + "; without "
    "it the log says that a ban can only expire.",
    "<b>PAM file.</b> " + c("guarda_il_servizio_pam()") + " looks for " + c("/etc/pam.d/remotix") + " and "
    + c("/usr/lib/pam.d/remotix") + ". It does not refuse to start, but without the file Linux-PAM falls back on "
    "the " + c("other") + " service — " + c("pam_deny") + " on Fedora and Arch, so every right password would be "
    "refused as if it were wrong — and the log says exactly that.",
    "<b>Certificates and TLS.</b> " + c("certificati_prepara()") + " loads or generates the two certificates in "
    + c("/var/lib/remotix/certificati") + ", then the two TLS contexts are built (one for QUIC, one for the page).",
    "<b>QUIC.</b> " + c("trasporto_apri()") + " binds the UDP port; then the hooks between transport and children "
    "are registered, the sentinel connects to the system bus, and the desktops left alive by a previous server "
    "are looked for (" + rif("Desktops found again after a restart") + ").",
    "<b>The page.</b> " + c("pagina_apri()") + " binds the TCP port. The log line " + c("⭐ pronto: https://NAME:PORT")
    + " (“ready”), which goes on to say that the WebTransport session lives on " + c("/rcp/1") + ", is the moment "
    "the server can be used.",
]) + \
    table(["Exit", "When"], [
        ["0", "orderly shutdown after " + c("SIGTERM") + " or " + c("SIGINT")],
        ["1", "the ban file cannot be read; certificates, TLS contexts, UDP port or TCP port cannot be prepared"],
        ["2", "usage error: unknown or retired option, missing " + c("--nome") + ", wrong " + c("--codifica")],
    ], "«TAB» — The server's exit codes") + \
    note("the server goes on when the PAM helper, the children table, the unblock socket, the sentinel or the "
         "codec probe fail, because the ban, the page and the certificates still work and stopping everything "
         "would put the blame on the wrong part. Each of these failures writes one line that names what will not "
         "work.", "Degrade, and say so.")

S2 = p("In a package the server runs as " + c("remotix.service") + ", a system unit. The packages install it but "
       "neither enable nor start it: " + c("remotix-install") + " does that once the installation is confirmed "
       "(" + rif("The installer") + ").", lead=True) + \
    code("""[Service]
Type=simple
ExecStart=/bin/sh -c 'exec /usr/libexec/remotix/remotix --indirizzo 0.0.0.0 --nome %H \\
    --porta "$${REMOTIX_PORTA}" --certificati /var/lib/remotix/certificati \\
    --pagina /usr/share/remotix/pagina.html --ban-file /var/lib/remotix/ban \\
    --journal $${REMOTIX_OPZIONI}'
KillMode=mixed
LimitRTPRIO=20
LimitNICE=-11
Restart=on-failure
RestartPreventExitStatus=78
RestartSec=2""", "text", "packaging/debian/remotix.service (excerpt, without the two EnvironmentFile lines)") + \
    table(["Setting", "Why"], [
        ["runs as root", "only root verifies any user's password with PAM and can become each user for their child"],
        [c("--nome %H"), "the certificate carries the machine's host name; whoever connects by IP address adds "
         + c("REMOTIX_OPZIONI=--nome 192.168.1.10") + " in a file of " + c("/etc/remotix/remotix.conf.d/")
         + " (the last " + c("--nome") + " wins)"],
        [c("EnvironmentFile"), "two of them: " + c("/usr/share/remotix/remotix.conf") + ", and the optional "
         "(leading " + c("-") + ") " + c("/etc/remotix/remotix.conf.d/*.conf") + "; they define "
         + c("REMOTIX_PORTA") + " (the port) and " + c("REMOTIX_OPZIONI") + " (extra options)"],
        [c("REMOTIX_PORTA"), "7447 by default, in " + c("/usr/share/remotix/remotix.conf") + "; the package's "
         "defaults are never edited, the administrator's choices go in " + c("/etc/remotix/remotix.conf.d/")],
        [c("/bin/sh -c 'exec …'"), "only to expand the variables; " + c("exec") + " keeps the server as the main "
         "process"],
        [c("KillMode=mixed"), c("SIGTERM") + " to the server alone, then " + c("SIGKILL") + " to whatever is left "
         "in the unit. The desktops are not in the unit, so they survive (measured in 10 trials out of 10 on 29 "
         "September 2026, four desktops)"],
        [c("LimitRTPRIO=20") + ", " + c("LimitNICE=-11"), "lets audio and video threads take a real-time priority, "
         "which the program then verifies"],
        [c("Restart=on-failure") + ", " + c("RestartSec=2"), "a crash restarts the server in 2 s; the desktops are "
         "found again"],
        ["no test options", c("--rilievo") + " (frame dump), " + c("--comando-socket") + " (unblock socket), "
         + c("--audio-prova") + " (test tone), " + c("--parlantina") + " (verbose log) and " + c("--sblocca")
         + " are not in the packaged command line; the rpm build script (" + c("costruisci-rpm.sh")
         + ") refuses them"],
    ], "«TAB» — The unit's settings") + \
    warn("with no " + c("--comando-socket") + " in the packaged command line, a banned address can only wait for "
         "its 12 hours: the unblock command promised by SPECIFICHE.md §4.2 is there only if the administrator adds "
         "the option in " + c("REMOTIX_OPZIONI") + " (the " + c("tmpfiles") + " entry creates "
         + c("/run/remotix") + " for that socket). No code path of the server exits with 78, so "
         + c("RestartPreventExitStatus=78") + " never applies today.", "Two gaps of the unit.") + \
    note("the server must not run inside a user's session. " + c("pam_systemd") + ", called by a process that is "
         "already in a logind session, does not create a second one and does not say so: the children stay without "
         "runtime directory, bus and desktop (measured 16 August 2026, eight bench runs out of eight). As a system "
         "unit this cannot happen; on the test machine " + c("riavvia-7700.sh") + " starts the server with "
         + c("systemd-run") + " and refuses to report success if " + c("/proc/PID/cgroup") + " shows a "
         + c("user@") + " or " + c("session-") + " cgroup.", "Started by hand.")

LOGIN = seq([("Page", "browser", "light"), ("Server", "root", "navy"), ("PAM helper", "one process per check", "dark"),
             ("Child", "the user", "blue"), ("Desktop", "compositor", "grey")], [
    (0, 1, "CIAO"),
    (1, 0, "ECCOMI: what the GPU encodes", True),
    (0, 1, "CREDENZIALI"),
    (1, 2, "case, user, password"),
    ("nota", 2, "pam_authenticate + pam_acct_mgmt"),
    (2, 1, "case, byte 1", True),
    ("nota", 1, "stages full? budget? then fork"),
    (1, 3, "fork, PAM session, execve"),
    (3, 1, "MSG_SONO", True),
    ("sep", "one second after the credentials arrived, for every answer"),
    (1, 0, "AMMESSO", True),
    (0, 1, "ATTACCA: canvas, view, layout"),
    (1, 0, "SESSIONE: new or resumed", True),
    (1, 3, "canvas, codec"),
    (3, 4, "setsid --fork: the desktop"),
    (3, 1, "MSG_TELA: wait", True),
    ("nota", 3, "retries every 200 ms"),
    (3, 4, "virtual monitor, stream"),
    (3, 1, "MSG_PALCO, frames", True),
    (1, 0, "one QUIC stream per frame", True),
], "«FIG» — From the password to the first frame", width=900)

S3 = p("A login crosses three processes. The page proves nothing until the server has shown its certificate; the "
       "password goes to a PAM process; the yes produces a child; only then does the client attach. The message names "
       "are those of " + c("RCP.md") + ": " + c("CIAO") + " (hello) and " + c("ECCOMI") + " (here I am), "
       + c("CREDENZIALI") + " (credentials), " + c("AMMESSO") + " (admitted), " + c("ATTACCA") + " (attach) and "
       + c("SESSIONE") + " (session).", lead=True) + \
    LOGIN + \
    p("<b>The verdict.</b> The server writes the request to the PAM helper and goes back to its loop ("
      + rif("The PAM helper process") + "). Every answer to " + c("CREDENZIALI") + " — admitted or refused — leaves "
      "no sooner than one second after the request arrived (" + c("RITARDO_FISSO") + "): without it “user does not exist” would "
      "answer in a millisecond and “wrong password” in fifty, and the stopwatch would tell what the reason code "
      "deliberately does not. Three failed checks from the same address within 5 minutes ban that address for "
      "12 hours, whatever the user names; a success resets the count; the ban survives restarts ("
      + rif("The RCP/1 protocol") + ").") + \
    p("<b>Yes is not yet in.</b> When the helper says yes, " + c("consegna_verdetto()") + " asks three questions, "
      "in this order, <b>before</b> anything is forked — a refusal after the desktop has started is not a refusal, "
      "it is a login followed by an eviction (measured 25 August 2026: a user never admitted had 42 processes and "
      "a " + c("gnome-shell") + "):") + \
    table(["Question", "If not", "Reason code"], [
        ["Does a stage still fit? Children plus found-again desktops below the cap", "no child; farewell",
         c("0x0E SESSIONE_NON_SERVIBILE") + " (the session cannot be served) — an administrative limit"],
        ["Does the composition budget allow one more canvas? (only with " + c("--budget-mpixel-s") + ")",
         "no child; farewell", c("0x06 BUDGET_PIENO") + " (budget full) — a physical limit"],
        ["Was the child born? (" + c("figli_assicura_da()") + ")", "the reason is in the line above in the log; "
         "farewell", c("0x0E")],
    ], "«TAB» — The checks between PAM's yes and the child") + \
    p("A user who already has a child, or a desktop found again, skips the first two: they are already counted, and "
      "their " + c("SESSIONE") + " will say <i>resumed</i> (2) instead of <i>new</i> (1). For a new child the "
      "abandonment clock starts now, at birth, not at the first gesture: a session opened and never touched must "
      "expire too. Then the verdict is handed to the transport, and only after it the farewell, if any: the verdict "
      "is the only place where the failure count of the ban is reset, and a farewell sent first would leave a "
      "user who typed the right password with their failures on record. The client never sees " + c("AMMESSO")
      + " followed by an eviction: " + c("AMMESSO") + " leaves only when the second has passed, and by then the "
      "session is already closed with its reason.") + \
    note("this tells whoever knocks that the password was right. It is the declared price of not leaving them in "
         "front of a black page, the same price paid when the attach table is full.", "The price.") + \
    p("<b>The child works during the second.</b> " + c("figli_assicura_da()") + " forks and returns at once: the "
      "child opens the user's logind session and its bus while the fixed second runs out, which is the only time "
      "the protocol guarantees before " + c("ATTACCA") + ".")

NASCITA = fig(
    box(30, 40, 180, 56, "Born", "MSG_SONO sent", "dark")
    + box(250, 40, 180, 56, "Waiting for canvas", "at most 1.2 s", "grey")
    + box(470, 40, 180, 56, "Desktop being born", "retry every 200 ms", "amber")
    + box(690, 40, 180, 56, "Stage mounted", "captures when asked", "green")
    + box(30, 200, 180, 56, "Exit", "from any state", "grey")
    + box(250, 200, 180, 56, "User logged out", "nothing restarts", "navy")
    + box(470, 200, 180, 56, "No stage", "retry 1 s, doubling to 30 s", "dark")
    + arrow(212, 68, 248, 68) + arrow(432, 68, 468, 68) + arrow(652, 68, 688, 68)
    + arrow(600, 98, 600, 198, "#475569") + text(606, 150, "after 12 s", 11, "#334155", "400", "start")
    + path([(652, 214), (720, 214), (720, 98)], "#16a34a") + text(726, 150, "retry ok", 11, "#334155", "400", "start")
    + path([(850, 98), (850, 242), (652, 242)], "#475569", True)
    + text(844, 176, "capture lost", 11, "#334155", "400", "end")
    + arrow(468, 228, 432, 228, "#475569") + text(450, 278, "session ended", 11, "#334155")
    + path([(330, 198), (330, 150), (520, 150), (520, 98)], "#003a90", True)
    + text(425, 142, "new attach with a codec", 11, "#334155"),
    900, 290, "«FIG» — The life of a child and its stage; it exits at logout, abandonment, MSG_SPEGNITI or when the server goes")

S4 = p("The child is born before it knows the canvas, and it must not start the desktop at the wrong size: on "
       "Wayland a resize completes only when the compositor delivers a new frame, and a fresh desktop changes "
       "nothing. Measured on 16 August 2026: starting at 1920×1080 and resizing 650 ms later left users looking at "
       "black bands for 13 to 30 seconds. So the child waits for the client's canvas, at most 1.2 s ("
       + c("TELA_ATTESA_MS") + "), then starts with what it has.", lead=True) + NASCITA + \
    p("Once running, " + c("figlio_vive()") + " introduces itself, prepares the dconf profile, removes leftovers of "
      "a previous session from the user manager (" + c("sessione_sgombera_gestore()") + ") and calls "
      + c("prendi_il_palco()") + ". That function connects to the user's session bus, reads the state of the "
      "graphical session and, if there is none, asks " + c("sessione_fai_nascere()") + " to start it.") + \
    table(["Step", "What " + c("sessione_fai_nascere()") + " does", "If it goes wrong"], [
        ["1", "refuses if no desktop was recognised, or if the session is not dead", "nothing is started twice"],
        ["2", "removes REMOTIX's drop-ins and environment left by a previous session, and saves a snapshot of the "
         "user manager's environment in " + c("$XDG_RUNTIME_DIR/remotix/gestore-prima"),
         "the next cleanup restores exactly what was there before"],
        ["3", "writes the drop-in that changes how the compositor starts (GNOME and KDE), and reads back that it is "
         "in force", "a GNOME session born with its own monitor is “healthy” for Mutter and black for us"],
        ["4", "refuses if the user manager is " + c("stopping") + " or the previous session's unit is not yet "
         "inactive", "a session born inside one that is dying dies with it without writing a line (measured: "
         "its log stays at zero bytes)"],
        ["5", "stops a " + c("pipewire-pulse") + " older than " + c("pipewire") + " (a leftover of the previous "
         "session)", "programs that play through PulseAudio would be mute"],
        ["6", "resets REMOTIX's dconf database (GNOME) and writes the session settings: power-off, reboot, "
         "suspend and lock removed, “Log out” present", rif("The four desktops")],
        ["7", c("avvia()") + ": " + c("setsid --fork sh -c 'exec >>LOG 2>&1; exec COMMAND'") + " with an "
         "environment built for the desktop", "the session's own output goes to "
         + c("~/.local/state/remotix/sessione.log")],
    ], "«TAB» — How a graphical session is started") + \
    table(["Desktop", "Command", "How the monitor gets the canvas"], [
        ["GNOME", "the distribution's own GNOME session (" + c("gnome") + ", " + c("ubuntu") + "…, read from the "
         "sessions the display manager offers), whose Shell unit gets a drop-in: " + c("gnome-shell --headless "
         "--no-x11") + " (plus " + c("--mode=%i") + " from GNOME 50), never " + c("--virtual-monitor"),
         "Mutter starts with no monitor; " + c("RecordVirtual") + " creates one at the canvas size"],
        ["KDE Plasma", c("exec startplasma-wayland") + "; the KWin unit's drop-in runs "
         + c("kwin_wayland_wrapper --xwayland --virtual --width W --height H --no-lockscreen"),
         "the virtual output is born at the canvas size"],
        ["XFCE", c("exec labwc -m --session") + " with " + c("xfce4-session") + " as primary client",
         "a small script runs " + c("wlr-randr --custom-mode") + " on the output before the session starts"],
        ["LXQt", c("exec labwc -C DIR -S") + " with " + c("lxqt-session") + ", DIR being REMOTIX's labwc "
         "configuration in the runtime directory", "the same " + c("wlr-randr") + " script"],
    ], "«TAB» — The four desktops, started (details in the chapter on the four desktops)") + \
    p("<b>The child does not wait for the desktop.</b> A child that waits 40 s does not answer the server, and the "
      "server would deduce a failure from its silence. Instead it tells the server “wait” (" + c("MSG_TELA")
      + " with " + c("attendi") + "), which postpones the answer to the client, and retries. While the desktop is "
      "being born — up to 12 s after asking (" + c("NASCITA_BRIGLIA_MS") + ") — it retries every 200 ms ("
      + c("PALCO_NASCITA_RIPROVA_MS") + "); after that the wait doubles from 1 s to 30 s ("
      + c("PALCO_RIPROVA_MIN_MS") + ", " + c("PALCO_RIPROVA_MAX_MS") + "). Both numbers were paid for: on 14 August "
      "2026 a loop that retried without pause wrote 30.8 GB of log in a few minutes; on 16 August a doubling wait "
      "made users wait up to four seconds for a session that was already up (GNOME appeared on the bus after about "
      "2.9 s on the test machine, and the tries fell at 3 s and then 7 s).") + \
    p("<b>First login: the GPU's groups.</b> A user who is not in the groups of the " + c("/dev/dri") + " nodes "
      "(" + c("card*") + " belongs to " + c("video") + ", " + c("renderD*") + " to " + c("render") + ") would get a "
      "session that renders in software with llvmpipe — slow, not broken, so nobody would suspect it. Since 20 "
      "September 2026 (DECISIONI.md §7.21) the server, as root, runs " + c("usermod -aG") + " for the missing groups "
      "before forking the child, appends one JSON line per group to " + c("/var/lib/remotix/gruppi-iscritti.jsonl")
      + " (so that uninstalling removes only what REMOTIX added) and, unless the user already has a live REMOTIX "
      "desktop, runs " + c("loginctl terminate-user") + " so that their user manager restarts with the new "
      "groups.") + \
    warn(c("loginctl terminate-user") + " ends <b>every</b> logind session of that user, an SSH login included. It "
         "only happens once per user, at their first REMOTIX login without the groups. Not settled yet: whether only "
         + c("render") + " should be added (" + c("video") + " also opens " + c("/dev/fb*") + " and webcams), "
         "DECISIONI.md §10.36.", "First login ends the user's other sessions.") + \
    p("<b>After the first stage</b> the child, once per life, inhibits suspend and idle (on GNOME through "
      + c("org.gnome.SessionManager.Inhibit") + " with flags 4|8, never the logout flag, or the user would lose their "
      "only way out; on KDE through PowerDevil; XFCE and LXQt by configuration), then asks the sentinel whether its "
      "session has no seat and whether power-off is forbidden, and writes both answers in the log. Written is not "
      "in force: the check is the program's, not a configuration line's (I7).")

S5 = p("The stage is what the child mounts on the user's desktop: a virtual monitor, the capture of its pixels, the "
       "input devices, the clipboard and the cursor. It belongs to the session and survives every client (I4).",
       lead=True) + \
    table(["", "GNOME (Mutter)", "KDE Plasma (KWin)", "XFCE, LXQt (labwc)"], [
        ["Virtual monitor", c("RemoteDesktop.CreateSession") + ", " + c("ScreenCast.CreateSession") + ", "
         + c("Session.Start") + ", " + c("RecordVirtual") + ", " + c("Stream.Start") + " — in this order",
         "the " + c("Virtual-0") + " output KWin was started with", "labwc's headless output"],
        ["Capture", "PipeWire node announced during " + c("Stream.Start"), c("zkde_screencast_unstable_v1")
         + " on " + c("Virtual-0") + ", then PipeWire", "wlr-screencopy, on the child's own loop"],
        ["Input", "libei through " + c("ConnectToEIS"), "libei through " + c("org.kde.KWin.EIS.RemoteDesktop"),
         "wlr virtual pointer and virtual keyboard"],
        ["Clipboard", "Mutter's RemoteDesktop session", "Wayland data control", "Wayland data control"],
    ], "«TAB» — What a stage is made of on each compositor") + \
    p(c("prendi_il_palco()") + " mounts these in order and times each step (a step over 250 ms is logged). It "
      "starts the capture on the GPU path (dmabuf, zero copy) and falls back to the memory path if the compositor "
      "refuses the format; it takes a first frame with a 5 s wait; on the very first mount it encodes that frame "
      "in HEVC and in H.264 to prove both streams; it reports everything to the server in " + c("MSG_PALCO")
      + " (bus, session state, capture result, monitor name and count, size, stride, bits per channel, streams "
      "encoded, failure in words); then it opens the cursor, the input channel — applying a keyboard layout that "
      "arrived before it — and the clipboard. On GNOME a monitor with a scale other than 1 is refused: the "
      "coordinates of input would no longer match the pixels.") + \
    p("<b>Why the child keeps everything open.</b> Measured on 27 August 2026 with a real Mutter: in headless mode "
      "the virtual monitor is born only when a PipeWire consumer attaches to the stream (65–93 ms after), survives "
      "the consumer detaching, and dies when the D-Bus connection that called " + c("RecordVirtual") + " closes. "
      "The child holds that connection and the stream for its whole life; when nobody is watching, it only stops "
      "taking frames. An application opened while no client is attached still has a screen to draw on.") + \
    p("<b>The capture loop.</b> While a codec is requested, each turn takes a frame with a wait of at most 8 ms. "
      "Mutter delivers only when something changes, so most turns on a still desktop find nothing; if a keyframe is "
      "owed and nothing came, the child wakes the compositor every 400 ms (" + c("RISVEGLIO_MS")
      + "), unless a key or button is held. A frame of a new size resizes the encoders and the input region, "
      "drops the kept keyframes and answers the server with the canvas obtained. A capture failure, or KWin "
      "closing its stream, unmounts the stage and the retry starts again. Every second the loop logs its counts: "
      "frames, keyframes, empty waits, failures.")

S6 = p("Detaching is the normal end of a connection, and it ends nothing else: the slot frees, the stage stays.",
       lead=True) + \
    table(["How the client goes", "What the server sees", "Reason"], [
        ["the tab or the browser closes, the device is switched off", c("CONGEDO") + " (farewell) from the page if it "
         "is in time, otherwise the QUIC connection dies", c("0x01 CHIUSO_DALL_UTENTE") + " (closed by the user), or "
         "none"],
        ["the network drops", "no packet for 30 s: the client is detached and its slot is free", "none"],
        ["no input for 30 minutes", "the server detaches the client; logging in again is needed",
         c("0x02 INATTIVITA")],
        ["the line cannot be served (stalled output for 5 s, or 10 s without a packet)", "the connection is "
         "closed", rif("Quality, degradation and budget")],
    ], "«TAB» — The ways a client detaches") + \
    p("In every case the keys still pressed are released in the desktop, so no key stays down after a drop. If no "
      "other client of the same user is watching, the server tells the child to stop capturing — "
      + c("MSG_VIDEO") + " and " + c("MSG_AUDIO") + " with codec 0 — and the child, the desktop, the monitor and "
      "the audio sink stay where they are. The farewell, the closed stream and the dead connection all lead to the "
      "same function, which is idempotent: the child is told once.") + \
    p("<b>Reattaching.</b> When the same user logs in again, " + c("figli_pid_di()") + " finds their child: no fork, "
      + c("SESSIONE") + " says <i>resumed</i>, and the server sends " + c("MSG_RIMANDA_PALCO") + " so that the "
      "child resends the last keyframe it kept for each codec — the user sees their desktop at once — and owes a new "
      "keyframe. The page then asks for its own canvas with " + c("ADATTA_TELA") + " (fit the canvas; " + rif("The browser page")
      + "). A reattach does not renew the abandonment clock: only input does.") + \
    table(["Situation", "Result"], [
        ["the user's previous client is alive and attached", "the new one is refused, " + c("0x0F GIA_ATTIVA_REMOTA")
         + " (already active remotely; I2)"],
        ["the previous client has been silent for more than 15 s and the new one is the same user",
         "the slot is taken from the ghost and given to the newcomer (" + c("--sfratto-ms") + " — eviction —, default 15000, "
         "half the silence clock: the browser's keep-alive is silent for up to 15 s, measured)"],
        ["the user has a local graphical session", "the attach is refused, " + c("0x05 GIA_ATTIVA_LOCALE")
         + " (already active locally)"],
        ["the user opens a local session while attached remotely", "the remote client is dismissed at the next sweep (every 2 s), "
         + c("0x04 SESSIONE_LOCALE_PREVALSA") + " (the local session prevailed; " + c("wt_sorveglia_locali()") + ")"],
    ], "«TAB» — One graphical session per user") + \
    note("SPECIFICHE.md §5.1 says that when a local session starts “the remote one is closed”. The code dismisses the "
         "remote <i>client</i>; the remote desktop is not ended and, if nobody touches it, ends with the abandonment "
         "clock.", "Local wins: what is closed.")

S7 = p("Stopping the server does not stop the desktops: the server, the PAM helper and the children die, while each "
       "desktop, started with " + c("setsid --fork") + " inside its user's logind session, keeps running with its "
       "programs (measured 29 September 2026, ten trials with Firefox on the four desktops: stopping the unit, "
       "killing only the server, killing only a child). Until phase 17 a new server started with an empty table and "
       "counted none of them — not in the cap, not in the budget, not on the abandonment clock.", lead=True) + \
    p("At startup " + c("ritrovati_all_avvio()") + " calls " + c("ritrovo_cerca()") + ", which uses only logind and "
      + c("/proc") + " — the server is root and cannot join the users' buses, and desktops started by an older binary "
      "wrote no file of ours:") + steps([
    "every logind session whose PAM service is " + c("remotix") + ", <b>in any state</b>: the child calls "
    + c("pam_end") + " without " + c("pam_close_session") + ", so the session is " + c("closing") + " 24 ms after "
    "birth and stays so as long as it has processes (measured 29 September 2026);",
    "in that session's scope, a process of the user that leads its own process session (pid = sid) and whose parent "
    "is not in the same scope: the signature of " + c("setsid --fork") + ", the same on every desktop — "
    + c("gnome-session-binary") + ", " + c("startplasma-wayland") + ", " + c("labwc") + ", all with parent 1. A "
    "terminal's shell also leads a session, but its parent is in the scope;",
    "one desktop per user; at most 256 (" + c("QUANTI_RITROVATI_MAX") + ").",
]) + \
    p("Each desktop found is logged and kept “waiting for reattach”: it counts in the cap and in the budget, and its "
      "abandonment clock restarts from the server's start (the last gesture seen by the old server was in its "
      "memory). When its user logs in, a new child is born — the old one died with the old server, by design — "
      "takes over the same compositor, and " + c("SESSIONE") + " says <i>resumed</i>. Every 10 s ("
      + c("RIPASSO_RITROVATI_MS") + ") the server checks that the desktops it found are still there, so that one "
      "that died on its own does not hold a place for an hour. If the clock expires with nobody back, the server "
      "forks a child just to close that desktop: only a process inside the user's bus can end a desktop properly, "
      "and desktops are closed, not killed.") + \
    tip("a package upgrade restarts the server with " + c("try-restart") + " only if it was running; the users' "
        "desktops survive and the new server finds them again. Before stopping the service by hand, look at who is "
        "connected anyway: their clients are dismissed with " + c("0x0C SERVER_IN_CHIUSURA") + " (server shutting "
        "down).", "Upgrades.")

S8 = p("Three clocks run on different scales — seconds, minutes, an hour — and each ends something different.",
       lead=True) + \
    table(["Clock", "Default", "Option", "What happens", "Reason"], [
        ["client silence", "30 s", "fixed (" + c("SILENZIO") + ", silence)", "the client counts as detached: its slot is "
         "free and the next device enters", "none"],
        ["user inactivity", "30 min", c("--inattivita-s") + " (0 = off)", "the client is detached; the desktop "
         "stays; user and password are needed again", c("0x02 INATTIVITA")],
        ["session abandonment", "60 min", c("--abbandono-s") + " (0 = off)", "the graphical session is closed with "
         "the programs inside", c("0x03 SESSIONE_ABBANDONATA")],
    ], "«TAB» — The three session clocks") + \
    p("<b>Silence</b> is measured on the last QUIC packet decrypted and authenticated, not on RCP bytes: counting RCP "
      "made a user who was only reading lose their slot after 30 s, and a second device take it while they looked "
      "(measured 16 August 2026). A switch from Wi-Fi to mobile data is not silence: QUIC carries the connection "
      "across the address change. A background tab frozen by the browser falls silent and detaches; the session "
      "waits.") + \
    p("<b>Input</b> means the five gestures a user sends — pointer, button, wheel, letter, key position — and "
      "nothing else: not the key release at detach (it would reset the clock at the wrong moment), not a canvas "
      "change, not the request to log out. " + c("input_al_figlio()") + " feeds the presence table of "
      + c("main.c") + "; " + c("abbandono_giro()") + " looks at it on every turn of the loop. The abandonment "
      "clock starts when the stage is born and is not renewed by reattaching: someone who attaches and only "
      "watches renews nothing (user decision, 16 August 2026, when the clock went from 6 hours without an attach "
      "to 60 minutes without input).") + \
    p("<b>Why an hour.</b> The user asked for the cost of an abandoned session to be measured first. On 16 August "
      "2026, on the test machine (31 GB of RAM), an abandoned GNOME session used 477 MB (PSS) — 182 MB of it "
      + c("gnome-shell") + ", 116 MB the child — and about 0.017 % of a core, without growing over time. Not a "
      "leak, a fixed cost; the user chose to pay it for an hour rather than six.") + \
    note("all three values are written in one log line at startup; a clock set to 0 is marked "
         + c("(SPENTA)") + " or " + c("(SPENTO)") + " (off).", "Logged at startup.")

USCITA = seq([("Page", "browser", "light"), ("Server", "root", "navy"), ("Child", "the user", "blue"),
              ("Desktop", "compositor", "grey")], [
    (0, 1, "TERMINA_SESSIONE"),
    (1, 0, "farewell 0x10 SESSIONE_TERMINATA to the user's other clients", True),
    (1, 2, "MSG_INPUT: end the session"),
    (2, 3, "polite logout, then forced"),
    ("nota", 2, "leftovers: SIGTERM, 2 s, SIGKILL"),
    ("nota", 2, "drop-ins and environment restored"),
    (2, 1, "exit 0", True),
    (1, 0, "farewell 0x10 (if still attached)", True),
], "«FIG» — Ctrl+Alt+End: the page asks, the child ends the desktop", width=900)

S9 = p("Only the user ends their session; the server ends it only when it is abandoned. Either way the reason is sent "
       "<b>before</b> the desktop dies: when the compositor goes, the stage goes with it, and a reason sent after "
       "reaches nobody (finding B-7).", lead=True) + \
    table(["How", "Path in the code", "Reason sent"], [
        ["“Log out” from the desktop's menu", "logind ends the session and with it the child, its leader; the "
         "server reaps the child and " + c("congeda_figlio()") + " dismisses the clients. If the child sees the "
         "session die first, it sends " + c("MSG_SESSIONE_FINITA") + " and the server does the same",
         c("0x10 SESSIONE_TERMINATA") + " (session ended)"],
        [c("Ctrl+Alt+End") + " in the page, after a confirmation", c("TERMINA_SESSIONE") + " (end the session) → "
         + c("termina_al_figlio()") + ": the user's other clients are dismissed, the child receives "
         + c("FIGLI_INPUT_TERMINA") + " and calls " + c("sessione_termina()"), c("0x10")],
        ["60 minutes without input", c("abbandono_scaduto()") + ": clients dismissed, then the same request to the "
         "child; for a desktop found again, a child is forked to close it", c("0x03 SESSIONE_ABBANDONATA")
         + " (session abandoned)"],
    ], "«TAB» — The ways a graphical session ends") + USCITA + \
    p(c("sessione_termina()") + " asks politely, then insists: on GNOME " + c("Logout") + " with mode 1, then mode 2 "
      "(forced); on KDE an orderly logout, then forced; on XFCE and LXQt the session manager's exit, then killing "
      "the compositor — each followed by a wait for the session to be really gone (up to 10 s). Then "
      + c("sessione_sgombera_scope()") + " sends " + c("SIGTERM") + " to whatever of the user is still in the "
      "child's own session scope, waits up to 2 s and sends " + c("SIGKILL") + " to the stubborn (on Ubuntu 26.04 "
      "with XFCE, " + c("localsearch-3") + " and an agent used to stay), and " + c("sessione_sgombera_gestore()")
      + " removes REMOTIX's drop-ins and puts the user manager's environment back as the snapshot recorded it. The "
      "child exits with 0.") + \
    p("<b>A logout is not followed by a rebirth.</b> A child that has seen its session alive and then dead remembers "
      "that the user left; it does not start the desktop again until a new attach requests a codec. Without this "
      "the desktop the user had just closed came back by itself a few seconds later (bench of 15 August 2026). The "
      "page goes back to the login form with its sentence for " + c("0x10") + " (the session has ended and its "
      "programs were closed), out of full screen and pointer lock.") + \
    note("" + c("0x01") + " promises “reattach and you will find everything”, which after a logout is false; "
         + c("0x10") + " exists so that the two endings never share a code (DECISIONI.md §4.1-quater).",
         "Why a new reason.")

S10 = p("When systemd stops the unit, the server says goodbye to every client before it closes QUIC, then lets its "
        "children go; the desktops stay.", lead=True) + steps([
    "The signal sets the flag; the loop ends and the log says how many QUIC connections are alive.",
    "Every RCP session receives " + c("CONGEDO 0x0C SERVER_IN_CHIUSURA") + " (" + c("trasporto_congeda_tutte()")
    + "). The server keeps reading and running timers until nothing is left to say, for at most 4 s by the clock "
    "(it used to count turns, which on a fast machine gave up after three tenths of a second while the safety "
    "net for the closing capsule was 3 s).",
    "Then, if every session has said all it had to say, it keeps the connections alive for another 50 turns of 10 ms: a capsule handed to ngtcp2 is not yet on "
    "the wire, and without this wait Firefox saw the service vanish with no reason (bench B7, 11 August 2026). "
    "The log says how many turns each phase took, or which connections still had something to say.",
    "Clean-up, in this order: the PAM helper (" + c("SIGTERM") + " to the dispatcher), the sentinel, the unblock "
    "socket, the page, the transport, the children — each receives " + c("SIGTERM") + " and is waited for — and the "
    "TLS contexts.",
]) + \
    p("A child also dies on its own when the server disappears, by two independent roads: " + c("PR_SET_PDEATHSIG")
      + " (which is lost when credentials change, so the child sets it again after " + c("execve")
      + ") and the end of file on its socket. The child's own " + c("SIGTERM") + " handler is the default one, so it "
      "dies without unmounting: the desktop keeps running and the next server finds it.") + \
    p("<b>When a child dies with the server alive</b> — a crash, a kill — " + c("congeda_figlio()") + " forgets the "
      "size of its stage and its presence entry, and dismisses its clients with " + c("0x10") + " unless the "
      "server itself is stopping (then " + c("0x0C") + " is the right reason, because the session will be found "
      "again). The server also kills a child that does not die within 3 s of being told to go.")

S11 = p("What REMOTIX puts on the machine, and who puts it there. Paths are those of the Debian package; the rpm "
        "and Arch packages use the same ones, except where noted.", lead=True) + \
    table(["Path", "From", "What"], [
        [c("/usr/libexec/remotix/remotix"), "package", "the binary: server, child and probe"],
        [c("/usr/share/remotix/pagina.html"), "package", "the page served on TCP"],
        [c("/usr/share/remotix/remotix.conf"), "package", "defaults: " + c("REMOTIX_PORTA=7447") + ", "
         + c("REMOTIX_OPZIONI") + " empty; never edited"],
        [c("/usr/share/remotix/incorporate.json"), "package", "versions of the static ngtcp2 and nghttp3 linked in, "
         "for the bill of materials"],
        [c("/usr/share/remotix/cinture/"), "package", "the three belts, <b>disabled</b>: the polkit rule, the logind "
         "keys, the sleep settings"],
        [c("/etc/remotix/remotix.conf.d/"), "administrator", "their choices, " + c("VARIABLE=value") + " lines"],
        [c("/etc/remotix/utenti-negati"), "package", "denied users: those PAM refuses outright; contains " + c("root")],
        [c("/etc/pam.d/remotix"), "package", "the PAM stack of the family (" + c("/usr/lib/pam.d/remotix")
         + " on openSUSE)"],
        [c("/usr/share/applications/org.kde.remotix.desktop"), "package", "lets KWin offer screen capture to the "
         "binary"],
        [c("/etc/ufw/applications.d/remotix"), "package (Debian)", "a firewall profile for 7447 TCP and UDP, defined "
         "but not opened"],
        ["the unit " + c("remotix.service"), "package", "installed, neither enabled nor started by the package"],
        [c("/var/lib/remotix/"), "tmpfiles, 0700 root", "the server's state"],
        [c("/var/lib/remotix/certificati/"), "server", c("pagina.pem") + "/" + c(".key") + " (365 days) and "
         + c("sessione.pem") + "/" + c(".key") + " (13 days, rotated 2 days before expiry); a " + c(".nostro")
         + " mark tells a generated certificate from the administrator's own"],
        [c("/var/lib/remotix/ban"), "server", "the banned addresses; survives restarts"],
        [c("/var/lib/remotix/gruppi-iscritti.jsonl"), "server", "one line per group REMOTIX added a user to; "
         "append-only, root-owned, " + c("fsync") + " after each line"],
        [c("/var/lib/remotix/") + " (other files)", "installer", "its records of the installation and of its "
         "operations (" + rif("The installer") + ")"],
        [c("/run/remotix/"), "tmpfiles, 0700 root", "for the unblock socket, when enabled"],
    ], "«TAB» — System files") + \
    table(["Path", "What", "Lives"], [
        [c("$XDG_RUNTIME_DIR/remotix/"), "per-session configuration: the user manager's snapshot ("
         + c("gestore-prima") + "), the dconf profile, KDE's " + c("kdeglobals") + "/" + c("kwinrc") + " overlay, "
         "labwc configurations for XFCE and LXQt, LXQt's panel overlay, a cursor theme", "until the user's last "
         "session ends (tmpfs)"],
        [c("$XDG_RUNTIME_DIR/systemd/user.control/"), "drop-ins: the GNOME Shell unit's or KWin's (to start "
         "headless or virtual), " + c("xfconfd") + "'s on XFCE", "removed by the cleanup"],
        ["the user manager's environment", "variables REMOTIX sets for the desktop (" + c("XDG_CURRENT_DESKTOP")
         + ", " + c("DCONF_PROFILE") + ", " + c("QT_QPA_PLATFORM") + "…)", "restored by the cleanup"],
        ["dconf " + c("service-db:shm/remotix"), "GNOME settings REMOTIX imposes for the session", "reset at every "
         "birth"],
        [c("~/.local/state/remotix/sessione.log"), "the desktop's own output", "kept; if the folder is not safe, "
         + c("$XDG_RUNTIME_DIR/remotix-sessione.log") + " instead, declared"],
    ], "«TAB» — Per-user files, written by the child") + \
    p("The user's own settings are not changed, with the exceptions DECISIONI.md §8.2 allows — lock, reboot, suspend and "
      "stand-by removed — detailed per desktop in " + rif("The four desktops") + ". The session log is created with "
      + c("O_NOFOLLOW") + " in a folder that must be the user's, not a link and not writable by others: until phase "
      "17 it lived in " + c("/tmp") + " under a predictable name, and another user could pre-create it.") + \
    warn("since DECISIONI.md §10.36 (10 October 2026) the installer no longer puts the belts in force: on a packaged "
         "machine nobody forbids power-off unless the administrator enables the files in "
         + c("/usr/share/remotix/cinture/") + ". The child checks and writes it in the log at every first stage; "
         "SPECIFICHE.md §11.3 still says power-off is taken from everyone.", "The belts are off by default.")

S12 = p("A defect in this chain rarely names its cause: the user sees “black”, “slow” or “nothing happens”. "
        "Start from the symptom, find the step, then read the log of the area that owns it.", lead=True) + \
    table(["Symptom", "Step to check", "Where"], [
        ["the login is refused for every user, right passwords included", "the PAM file; " + c("utenti-negati")
         + " missing makes " + c("pam_listfile") + " refuse everyone", c("guarda_il_servizio_pam()") + " line at "
         "startup; the " + c("PAM NON HA POTUTO GIUDICARE") + " (PAM could not judge) line"],
        ["the desktop never appears", "the logind session (the child's first line: runtime directory and bus "
         "present?); the server started inside a user session; no desktop recognised", c("figlio") + " area; "
         + c("MSG_SONO") + " line"],
        ["it appears after many seconds", "a previous session still dying (the child waits for it); the birth window",
         c("sessione") + " area: " + c("non e' ancora finita") + " (not yet over)"],
        ["black bands, a “broken” desktop, clicks in the wrong place", "the canvas: the stage was born at a size "
         "nobody asked for", c("MSG_TELA") + " lines, chosen and obtained"],
        ["everything is slow, even typing in a terminal", "the GPU's groups: the compositor renders with llvmpipe",
         "first-login lines of the " + c("figlio") + " area"],
        ["the desktop shows but does not react", "the input channel (libei, KWin EIS, wlr virtual devices)",
         c("input") + " area lines after the stage"],
        ["the machine can be powered off from the session", "the belts", "the child's power-off line"],
        ["a user logged out and the desktop came back", "the three-state rule after logout", c("figlio")
         + " area"],
        ["a user is refused with " + c("0x0E") + " (the session cannot be served)", "stages full: children plus desktops found again, "
         "which last until logout or abandonment", "the " + c("0x0E") + " line with the counts"],
    ], "«TAB» — From symptom to step")

CHAPTER = ("Startup and life cycle", [
    ("Server startup", S1),
    ("The systemd unit", S2),
    ("From password to admission", S3),
    ("Birth of a session", S4),
    ("The stage and the virtual monitor", S5),
    ("Detach and reattach", S6),
    ("Desktops found again after a restart", S7),
    ("The three session clocks", S8),
    ("Ending a graphical session", S9),
    ("Server shutdown and cleanup", S10),
    ("Files on the machine", S11),
    ("From symptom to step", S12),
])
