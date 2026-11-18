from build import c, code, h4, note, p, rif, steps, sysf, table, tip, ul, warn

# ── The log module ───────────────────────────────────────────────────────
FUNCTIONS = table(["Function / macro", "Writes", "Used by"], [
    [c("registro_dice(area, fmt, …)"), "An event line, always", "Every module. The name is Italian for «the log "
     "says»; it is a macro over " + c("log_says_in()") + " that adds " + c("__FILE__") + " and " + c("__LINE__")],
    [c("log_detail(area, fmt, …)"), "A detail line, only when " + c("--verbose") + " is on",
     "Transport, capture, input, clipboard, the child's frame loop: lines that are many and useful only while "
     "hunting a defect"],
    [c("log_says_of(area, who, fmt, …)"), "An event line that carries the identity of one user",
     "The parent, which serves all sessions at once (" + c("webtransport.c") + ", " + c("rcp.c") + " through "
     + c("hook_log()") + ", the parent half of " + c("child.c") + ")"],
    [c("log_detail_of(area, who, fmt, …)"), "The same, detail level", "The parent"],
    [c("log_identity(who)"), "Nothing: sets the identity of the whole process",
     "The per-user child, as soon as it has read its own " + c("argv")],
    [c("log_chatter(on)") + " / " + c("log_verbose()"), "Nothing: switches and reads the detail level",
     c("main.c") + ", " + c("helper.c") + " and " + c("child.c") + " (option " + c("--verbose") + ")"],
    [c("log_journal(on)") + " / " + c("log_to_journal()"), "Nothing: opens, closes and reads the state of the "
     "journal socket", c("main.c") + ", " + c("helper.c") + ", " + c("child.c") + ", " + c("rootside.c")
     + " (option " + c("--journal") + ")"],
    [c("log_speakable_key(code)"), "Nothing: says whether a key code may be written", c("input.c")],
    [c("log_now_ms()"), "Nothing: monotonic milliseconds", "RCP clocks, ban, per-user clocks"],
], "«TAB» — The interface of " + c("src/log.h"))

S1 = p("Every line the server writes goes through one module, " + c("src/log.c") + ". The four writing functions are "
       "macros over four " + c("_in") + " functions that add the source file and line, and all of them end in one "
       "static function, " + c("line()") + ". There is no scattered " + c("printf") + " in the server.",
       lead=True) + \
    p("The reason is written at the top of " + c("log.h") + ": a log spread over many " + c("fprintf(stderr, …)")
      + " has neither a timestamp nor an area, and those two are what make a line readable to whoever hunts a "
      "defect hours later. The second reason is a security check: the review item B13.2 asks that the password "
      "appear in no log, and a single funnel makes «it is not there» verifiable (" + rif("What never enters the log")
      + "). " + c("docs/LESSONS.md") + " §2.7 calls the log the main diagnostic instrument of the project.") + \
    FUNCTIONS + \
    note("a few places write straight to " + c("stderr") + " and are outside the funnel: " + c("authentication.c")
         + " (the PAM check, lines prefixed " + c("RCP:") + "), the child between " + c("fork") + " and "
         + c("exec") + " (" + c("become_and_exec()") + ", lines prefixed " + c("child:") + "), the usage text and "
         "the refusals of the command line in " + c("main()") + ", and the KDE start-line helper "
         + c("kwin_nested_alive()") + " (lines prefixed " + c("remotix --kwin-nested:") + "), which runs as the "
         "user inside KWin's unit. These lines have no timestamp, no area and never reach the journal through "
         + c("--journal") + ".", "Outside the funnel.")

# ── Anatomy of a line ────────────────────────────────────────────────────
S2 = p("A line is " + c("HH:MM:SS.mmm area [identity] body") + ": local wall-clock time with milliseconds, the "
       "area left-aligned in seven columns (" + c("%-7s") + "), the identity in brackets only when there is one, "
       "then the body.", lead=True) + \
    table(["Rule", "Value", "Why"], [
        ["One " + c("write(2)") + " per line", "Header, body and newline in one buffer of 4096 bytes (" + c("buf[4096]")
         + " in " + c("line()") + ")",
         "The parent and the child append to the same stream. A line written in several calls could be split by "
         "another process; the comment in " + c("line()") + " reports 23 orphan lines (lines with no timestamp) in "
         "a real log of 28,035 lines before the rule. A line below " + c("PIPE_BUF") + " written in one append "
         "write is atomic with respect to the others."],
        ["Truncation is declared", "A body that does not fit ends with " + c("...") + " before the newline",
         "A cut line can be seen; an interleaved line cannot."],
        ["No control bytes in the body", "Every byte below 0x20, DEL, the C1 controls, the bidirectional "
         "controls, U+2028/U+2029 and the invisible characters U+2060–U+2064 and U+FEFF become " + c("?"),
         "A value written by someone else (a request target, a user name) with a newline in it would forge a "
         "second line that looks like the server's. Valid UTF-8 otherwise passes untouched."],
        ["Identity at the head of the body", c("[name] ") + " after the area",
         "Readers split a line into time, area and body; a field between time and area would shift the area."],
        ["Identity sanitised", "Only " + c("0-9 A-Z a-z . _ - @ :") + "; anything else becomes " + c("_")
         + "; at most " + c("LOG_IDENTITY_MAX") + " characters (48)",
         "A " + c("]") + " or a newline in a name would split the line into two plausible and false lines."],
        ["No identity, no brackets", "The line goes out without " + c("[]"),
         "Not knowing is an outcome. The measurement behind it is in " + rif("Whose line it is") + "."],
        ["Write errors are not reported", "No place to report them",
         "The only channel would be the broken one; " + rif("Where the log lines go") + " says what is done "
         "when " + c("stderr") + " does not accept a line."],
    ], "«TAB» — How " + c("line()") + " builds a line") + \
    p("The body follows one convention across the code: a body that <b>starts</b> with " + c("⛔") + " is a fault, "
      "with " + c("⚠") + " a declared fallback or a warning, " + c("⭐") + " marks a notable fact (a decision in "
      "force, a cure that fired). Only the mark at the head counts, because many normal lines quote a " + c("⛔")
      + " in the middle; the journal priority reads only the head (" + rif("Journal priorities and the rule of the head mark")
      + ").") + \
    code("08:41:07.312 startup ⭐ ready: https://server.lan:7447 …\n"
         "08:41:19.884 rcp     [anna] … PAM answered …\n"
         "08:41:21.040 child   [anna] ⭐ …",
         "text", "Shape of three lines (text abbreviated; the real bodies are longer)") + \
    p("The time is " + c("CLOCK_REALTIME") + " in local time, for the human reader. Every interval the code "
      "measures uses " + c("log_now_ms()") + " (" + c("CLOCK_MONOTONIC") + "); the two are never mixed.")

# ── Areas ────────────────────────────────────────────────────────────────
S3 = p("The area is the second column of every line and the " + c("REMOTIX_AREA") + " field in the journal. It "
       "exists to read the log by column when transport, protocol and session speak at the same time. The names "
       "below are the string values; the constants are defined in " + c("log.h") + " unless said otherwise.",
       lead=True) + \
    table(["Area", "Constant", "Written by"], [
        [c("startup"), c("LOG_STARTUP"), "Startup and shutdown of the parent (" + c("main.c") + ")"],
        [c("quic"), c("REG_QUIC"), "QUIC and TLS (" + c("transport.c") + ", " + c("tls.c") + ")"],
        [c("wt"), c("REG_WT"), "HTTP/3 and WebTransport, the parent's half of every session (" + c("webtransport.c") + ")"],
        [c("rcp"), c("REG_RCP"), "The RCP state machine (" + c("rcp.c") + "), the PAM helper's parent side ("
         + c("helper.c") + "), the bench-only command socket (" + c("command.c") + "; the packaged service never opens it)"],
        [c("page"), c("LOG_PAGE"), "The TCP page server (" + c("page.c") + ")"],
        [c("cert"), c("REG_CERT"), "Certificates (" + c("certificates.c") + ")"],
        [c("session"), c("LOG_SESSION"), "Birth, settings and end of the desktop session (" + c("session.c") + "), the "
         "local-session guardian (" + c("sentinel.c") + ")"],
        [c("video"), c("REG_VIDEO") + "; " + c("LOG_ENCODING") + " in " + c("encoder.c") + ", " + c("vadirect.c")
         + ", " + c("vulkanvideo.c"), "Video encoding (" + c("LOG_ENCODING") + " is a local alias of the same text)"],
        [c("budget"), c("REG_BUDGET"), "The composition budget (" + c("budget.c") + ")"],
        [c("rootside"), c("LOG_ROOT") + " in " + c("rootside.c"), "The root side of the split server"],
        [c("child"), c("LOG_CHILD") + " in " + c("child.h"), "The per-user child and the parent's child table ("
         + c("child.c") + "); " + c("render_grant.c") + " uses the same text as " + c("LOG_GRANT")],
        [c("audio"), c("REG_AUDIO") + " in " + c("audio.c"), "The Opus encoder"],
        [c("sound"), c("LOG_SOUND") + " in " + c("sound.c"), "The PipeWire sink of the session"],
        [c("clipboard"), c("LOG_CLIPBOARD") + " in " + c("clipboard.h"), c("clipboard.c") + ", " + c("clipboard_kde.c")],
        [c("keyboard"), c("LOG_KEYBOARD") + " in " + c("keyboard.c"), "Keyboard layouts and keymaps"],
        [c("capture"), c("AREA") + " (local define)", c("capture.c") + ", " + c("mutter.c") + ", " + c("kwin.c") + ", "
         + c("wlroots.c")],
        [c("input"), c("AREA") + " (local define)", c("input.c") + ", " + c("wlr_input.c")],
        [c("cursor"), c("AREA") + " (local define)", c("cursor.c")],
        [c("shape"), c("AREA") + " (local define)", c("shape.c")],
        [c("log"), "literal string in " + c("log.c"), "The notice that lines were dropped because " + c("stderr")
         + " did not accept them"],
    ], "«TAB» — The log areas") + \
    note("the area is padded to seven characters; " + c("session") + ", " + c("keyboard") + ", " + c("rootside")
         + " and " + c("clipboard") + " are longer and push the body to the right. A tool that parses the log must "
         "split on white space, not on column positions.")

# ── Whose line it is ─────────────────────────────────────────────────────
S4 = p("With several users on one machine, a line that does not say whose it is sends the reader to look at "
       "somebody else's desktop. The identity in brackets is the user name, and it reaches the line by two roads "
       "because the processes are of two kinds.", lead=True) + \
    table(["Process", "How the identity arrives", "Effect"], [
        ["The per-user child: serves <b>one</b> session", c("log_identity()") + " from " + c("argv") + ", as the first "
         "thing the child does", "Every line of that process carries the name, including lines of " + c("encoder.c")
         + " and " + c("audio.c")],
        ["The parent: serves <b>all</b> sessions", "Per line: " + c("log_says_of(area, who, …)"),
         "A process-wide identity would always say the same thing, i.e. nothing. The per-line name wins over the "
         "process one; with neither, the line has no brackets."],
    ], "«TAB» — Two kinds of process, two roads for the identity") + \
    p("The comment in " + c("log.h") + " records the measurement behind this (finding R10-A4): with four real GNOME "
      "sessions (57,121 lines in 90 s) only 4.2 % of the diagnostic lines said whom they were about, and a reader "
      "who guessed the name was wrong 96 times in 100. The identity is composed in one place only, " + c("line()")
      + "; the callers pass the bare name. It is stored as a <b>copy</b> in a static buffer of the process, not as a "
      "pointer, and it does not cross " + c("exec") + ", which is why the child sets it again from its own command "
      "line.") + \
    warn("the bracket of a line written by the parent for a login attempt is the name the client <b>claimed</b>, also "
         "before PAM has answered. The server therefore does not write that name as such: "
         + c("log_user()") + " in " + c("rcp.c") + " writes " + c("user [a1b2c3]") + " (or " + c("unknown user [a1b2c3]")
         + " when the name is not a user of the machine), where the six hex digits are the first three bytes of an "
         "HMAC-SHA256 of the name under a secret kept in the file " + c("log-secret") + " (mode 0600). The same tag "
         "reaches the PAM helper through " + c("REMOTIX_PAM_LOG_TAG") + " (" + rif("Environment variables read by the product")
         + "). Read the outcome line, not the bracket, to know who got in.", "A claimed name is not an authenticated name.")

# ── Where the lines go ───────────────────────────────────────────────────
S5 = p("The log has no file of its own: the server writes to its standard error, and the unit that starts it decides "
       "where that goes. The child inherits descriptors 0, 1 and 2 across " + c("exec") + ", so parent and child "
       "lines land in the same stream and can be read in order.", lead=True) + \
    table(["Stream", "Where it ends up", "Notes"], [
        ["Parent, root side, PAM helper and child " + c("stderr"), "Packaged service: the unit's output, i.e. the "
         "journal under " + sysf("remotix.service") + " (" + c("debian/remotix.service") + ")",
         "The service starts the server with " + c("--journal") + " in " + c("ExecStart") + ", so event lines are "
         "also sent natively; see " + rif("The systemd journal output") + "."],
        ["Native journal datagrams", sysf("/run/systemd/journal/socket"), "Only with " + c("--journal") + "; the "
         "root side, the PAM helper and the child receive the option on their command lines."],
        ["PAM grandchild messages", "Same " + c("stderr"), "Lines start with " + c("RCP:") + " (" + c("authentication.c")
         + "); no timestamp, no journal fields."],
        ["Desktop session output", sysf("$XDG_STATE_HOME/remotix/session.log") + " (normally "
         + sysf("~/.local/state/remotix/session.log") + ")", "Written by the shell that starts the session; see "
         "below."],
    ], "«TAB» — The streams and their destinations") + \
    h4("A stderr that never blocks the loop") + \
    p(c("stderr") + " under systemd is journald's stream socket, which is blocking. The child's single loop "
      "delivers every frame, so a stalled journald must not stop it. " + c("err_write()") + " in " + c("log.c")
      + " therefore never waits: it looks at descriptor 2 at every line (" + c("err_look()") + ") and writes "
      "without waiting when it can block. On a socket it uses " + c("send(MSG_DONTWAIT)") + " and refuses to "
      "start a line the send buffer cannot take whole (" + c("SIOCOUTQ") + " against " + c("SO_SNDBUF") + ")."
      " On a pipe it opens " + sysf("/proc/self/fd/2") + " a second time with " + c("O_NONBLOCK") + " (not "
      + c("fcntl") + " on descriptor 2, which would change the open file for the shell that shares it). A file or "
      "a terminal is written as usual. A line that does not fit is <b>dropped and counted</b>, and as soon as "
      "the stream accepts again the count is written: " + c("log     ⚠ N log lines DROPPED: stderr was not accepting") + " "
      "(" + c("dropped_notice()") + "). A hole in the log is therefore declared instead of the loop stopping. "
      "A line cut in the middle by a stream socket is closed with the mark " + c("…[line cut: stderr full]") + ".") + \
    h4("The session log") + \
    p("Whatever the desktop session itself prints goes to a file chosen by " + c("log_session_path()") + " in "
      + c("session.c") + ": " + sysf("session.log") + " in the folder " + sysf("remotix") + " under the user's state "
      "directory (" + c("g_get_user_state_dir()") + ", normally " + sysf("~/.local/state") + "). The shell command "
      "that starts the session begins with " + c("exec >>FILE 2>&1") + " (in " + c("start()") + "). The folder "
      "is created with mode 0700 and must be a real directory (not a link), owned by the user and not writable by "
      "others (" + c("is_our_dir()") + "); the file is opened with " + c("O_NOFOLLOW") + ", mode 0600, and must be "
      "a regular file of the user (" + c("our_file()") + "). If that cannot be done the fallback is "
      + sysf("$XDG_RUNTIME_DIR/remotix-session.log") + ", which disappears with the session, and the server says so "
      "with a " + c("⚠") + " line; if even that fails the session starts with " + c("exec >/dev/null 2>&1") + " and "
      "a " + c("⛔") + " line says that the session has no log. The reason for the location is in the comment of "
      + c("log_session_path()") + ": a predictable name in a shared directory could be created first by another "
      "user, and a log in " + c("XDG_RUNTIME_DIR") + " would be gone exactly when a session that died at once needs "
      "it. The package removes the file when the package is purged (" + c("debian/remotix.postrm") + ").")

# ── The journal output ───────────────────────────────────────────────────
S6 = p("With " + c("--journal") + " every event line also goes to the systemd journal, with fields that can be "
       "filtered. The line on " + c("stderr") + " keeps its text; the journal is added, not substituted (except where "
       + c("stderr") + " is itself the journal, as under the packaged unit: «No second copy» below). The packaged "
       "service always passes " + c("--journal") + ".", lead=True) + \
    table(["Field", "Content", "Query"], [
        [c("MESSAGE"), "The line without the time (the journal stamps its own), sent in the binary form (name, "
         "newline, 64-bit little-endian length, bytes), the only form that survives a newline inside the value", ""],
        [c("PRIORITY"), "3, 4 or 6 from the head mark of the body (" + rif("Journal priorities and the rule of the head mark")
         + ")", c("journalctl -t remotix -p warning")],
        [c("SYSLOG_IDENTIFIER"), c("remotix"), c("journalctl -t remotix")],
        [c("REMOTIX_AREA"), "The area (" + rif("Log areas") + ")", c("journalctl -t remotix REMOTIX_AREA=rcp")],
        [c("REMOTIX_TENANT"), "The sanitised identity; the field is absent when the line has none",
         c("journalctl -t remotix REMOTIX_TENANT=anna")],
        [c("CODE_FILE") + ", " + c("CODE_LINE"), "Source file and line of the call", ""],
    ], "«TAB» — The journal fields") + \
    table(["Choice", "Why"], [
        ["Native protocol, no " + c("libsystemd"), "One datagram per line on " + sysf("/run/systemd/journal/socket")
         + " (" + c("al_journal()") + "): no new dependency."],
        [c("SOCK_NONBLOCK") + " and " + c("MSG_DONTWAIT") + ", errors ignored", "A clogged, stopped or absent "
         "journal (a container) must not cost a line nor stop the loop: " + c("stderr") + " has the line anyway."],
        [c("sendmsg") + " with the address every time, never " + c("connect"), "A connected datagram socket stays "
         "dead if journald restarts; an unconnected one finds the new journald at the next datagram."],
        ["Socket opened once, at switch-on", c("line()") + " runs in several threads; two threads opening it "
         "together would leak a descriptor."],
        [c("SOCK_CLOEXEC"), "The child is an " + c("execve") + " and opens its own socket; it learns about the "
         "journal from " + c("--journal") + " on its command line, like " + c("--verbose") + ". The root side closes "
         "the journal in the fork before moving descriptors and opens it again after (" + c("rootside.c") + ")."],
        ["Detail lines are not sent", "With many sessions they are tens of thousands per minute (the comment in "
         + c("line()") + "); the journal's rate limit would drop exactly the events. The journal keeps the events, "
         "the detail stays in the stream."],
        ["No second copy on stderr", "When " + c("stderr") + " is itself journald's stream (" + c("stderr_is_journal()")
         + ": the " + c("JOURNAL_STREAM") + " variable matches descriptor 2, or the peer of descriptor 2 is under "
         + sysf("/run/systemd/journal/") + ") and the native send succeeded, the line is not written to "
         + c("stderr") + " a second time. When the send fails, or the line is a detail line, " + c("stderr")
         + " carries it."],
    ], "«TAB» — Design choices of the journal output") + \
    p("The child, after " + c("pam_open_session") + ", lives in the scope of the user's logind session, not in the "
      "server unit, so " + c("journalctl -u remotix") + " does not find its lines; query by identifier.") + \
    code("journalctl -t remotix -f                         # everything, parent and children\n"
         "journalctl -t remotix -p warning --since today   # faults and fallbacks only\n"
         "journalctl -t remotix REMOTIX_TENANT=anna        # one user\n"
         "journalctl -t remotix REMOTIX_AREA=budget        # why somebody was refused\n"
         "journalctl -t remotix -o verbose -n 1            # every field of the last line",
         "bash", "Reading the journal") + \
    p("At startup the parent declares the outcome: " + c("log also in the systemd journal (--journal): …") + " or "
      + c("⚠ --journal requested but the socket does not open (…): the log stays ONLY here") + ". The journal is "
      "switched on before the first line, so the first line goes there too.") + \
    note("the box in " + c("log.h") + " says priority 7 is used for the chatter. The code in " + c("line()") + " never "
         "sends detail lines to the journal, so 7 does not occur; the help text of " + c("main.c") + " says the same "
         "as the code. The code is right.", "Priority 7.")

# ── Journal priorities ───────────────────────────────────────────────────
S6B = p("The priority of a line is decided in " + c("line()") + " by the first non-blank characters of the body: "
        + c("⛔") + " gives 3 (error), " + c("⚠") + " gives 4 (warning), anything else 6 (info). The file "
        + c("docs/REGISTRO-priorita.md") + " records the pass of 17 Nov 2026 (31 lines of code changed) that moved lines between the "
        "levels by changing <b>only the mark at the head</b> of the body; text, logic and the " + c("log_detail")
        + " levels were left alone. The aim was that " + c("journalctl -b -p err") + " should contain only what needs "
        "a person. The counts below come from that document (a full run on the four test containers) and were "
        "not re-measured for this manual.", lead=True) + \
    table(["Class", "Examples (source file)", "New level"], [
        ["Routine reports of a normal life cycle", "the child's birth report " + c("child.c") + "; the child leaving at "
         "logout " + c("main.c") + "; " + c("FRAME NOT SENT: … wants a KEYFRAME") + " (" + c("rcp.c") + "); "
         + c("CLIENT FIN on the control channel") + " (" + c("webtransport.c") + ")", "info"],
        ["Expected, handled, the session goes on", "frame over the ceiling or thrown away before the wire (" + c("rcp.c")
         + "); the rate drops and a keyframe debt (" + c("webtransport.c") + "); audio FIFO not obtained, audio "
         "capture detached; no stream from KWin, no virtual monitor, no stage at birth, zero monitors (the session "
         "is not ready and is retried); the compositor closed the input channel; an address still banned; "
         "a refused login for a name that is not a user (" + c("rootside.c") + ")", "warning"],
        ["Action wanted by whoever drives a bench", c("UNBLOCKED on command") + " (" + c("command.c") + "; only with the bench "
         "option " + c("--command-socket") + ", which the package never passes: there is no administrator unblock "
         "command)", "info"],
        ["Kept as error", c("NO VIDEO: no codec negotiated") + " (a protocol violation); a new ban of an address or "
         "user (" + c("rcp.c") + "); " + c("R2: N passwords … refused by PAM") + " (" + c("rootside.c") + "); "
         + c("FROM THIS SESSION THE MACHINE CAN BE POWERED OFF OR SUSPENDED") + " (" + c("child.c") + ", the "
         "safety belt of SPECS §4.7)", "error"],
    ], "«TAB» — The classes of the priority pass") + \
    p("The document counts 33 patterns seen in the run: 5 moved to info, 24 to warning, 4 kept as error. It lists "
      "what is not ours and was left alone (for example the " + c("pam_env") + " message about a missing "
      + sysf("/etc/default/locale") + " in the test image, rtkit and colord messages in containers).") + \
    warn("two things the document itself leaves open. (1) On the test containers " + c("POWERED OFF OR SUSPENDED")
         + " appears as an error because logind answers " + c("CanSuspend=(no answer)") + " there and the check "
         "counts that as a failure; it was kept as an error because it is the safety belt, and changing it "
         "would need a decision on the logic of the guardian (" + c("sentinel.c") + "). (2) About 700 call sites "
         "start with " + c("⛔") + " and did not occur in the run, so their level is unverified; the document names "
         "the quality-down line of " + c("encoder.c") + " (a bandwidth adaptation) as a candidate for " + c("⚠")
         + ". The warning level was not measured in depth.", "Open points of the priority pass.")

# ── What never enters the log ────────────────────────────────────────────
S7 = p("Three things never enter any log at any level: passwords, what the user types, and the content of the "
       "screen. The first is a protocol rule (RCP.md, see " + rif("The RCP/1 protocol") + "), the second a "
       "decision of phase 16 recorded in " + c("log.h") + " (keystrokes are logged as «key», never as a character), "
       "the third follows: the only images the server can write are those of the bench option " + c("--survey")
       + ", which is off by default.", lead=True) + \
    table(["What", "Rule in the code", "Where"], [
        ["The password", "Never formatted into a line, not even its length. The local copy is wiped with "
         + c("explicit_bzero()") + " once PAM has answered, and the copies in the PAM helper's request are wiped after use",
         c("rcp.c") + ", " + c("helper.c")],
        ["The PAM conversation copy", "Duplicated with " + c("strdup") + " for libpam, which owns and frees it; the "
         "comment in " + c("conversation()") + " says Linux-PAM overwrites it before freeing (measured 10 Aug 2026)",
         c("authentication.c")],
        ["The name of a user who failed to log in", "Written as a six-hex HMAC tag, not as text (" + rif("Whose line it is") + ")",
         c("log_user()") + ", " + c("rcp_log_tag()") + ", " + c("name_for_log()")],
        ["Typed characters", "Written as «a character» or «key pressed/released»; never the character or its code point",
         c("rcp.c") + ", " + c("keyboard.c") + ", " + c("input.c")],
        ["Key codes", "Only the modifiers keep their evdev code (Ctrl 29/97, Shift 42/54, Alt 56/100, CapsLock 58, "
         "Meta 125/126): they say nothing about the text and are the keys that get stuck",
         c("log_speakable_key()") + " and its twin " + c("speakable_key()") + " in " + c("rcp.c")],
        ["Text from the client in the page server", "The request target quoted in the " + c("GET … from") + " line is "
         "reduced to printable ASCII and cut at " + c("PAGE_LOG_TARGET") + " bytes with its length said",
         c("log_clean()") + " in " + c("page.c")],
        ["Control bytes of any text", "Turned into " + c("?") + " (" + rif("Anatomy of a log line") + ")", c("line()")],
        ["Session identities", "Sanitised to user-name characters", c("line()")],
    ], "«TAB» — The exclusions and where they are enforced") + \
    p("A sequence of evdev codes such as " + c("30, 48, 46") + " is a word: a key code <b>is</b> a character up to the "
      "keyboard layout. That is why the list of speakable keys is the only question a caller must ask before writing "
      "a code. " + c("rcp.c") + " carries its own copy because it is also compiled into a test host that has no "
      "server log.") + \
    note("the PAM check in " + c("authentication.c") + " writes to " + c("stderr") + " and so it never goes "
         "through " + c("line()") + ": its lines (" + c("RCP: PAM REFUSED …") + ", " + c("RCP: ⛔ PAM COULD NOT JUDGE …")
         + ") are the ones to read when a login is refused. The first means PAM said no; the second means PAM could "
         "not judge (for example a missing PAM service file). The client receives the same refusal in both cases.",
         "Two different PAM lines.")

# ── Startup declarations ─────────────────────────────────────────────────
S8 = p("At startup the parent writes the value <b>in force</b> of every mechanism that changes what users see or "
       "that can close a session, whether switched on or off. A threshold that is off and a threshold that never "
       "fired produce the same log, and a long clock is never verified by waiting for it, so the line is the "
       "verification. The order is that of " + c("main()") + "; the table lists what is declared and which function "
       "writes it.", lead=True) + \
    table(["Declaration (area)", "Written by"], [
        ["Product banner, then whether the journal is on (" + c("startup") + ")", c("main.c")],
        ["The codecs this server can encode, or " + c("⛔⛔ THIS SERVER CANNOT ENCODE VIDEO") + " with the reason; "
         "and the retries while the card is not ready yet (" + c("startup") + ")", c("child_video_capabilities()") + ", "
         + c("codec_step()") + ", " + c("codec_retry()")],
        ["Which desktop the machine has and why (" + c("startup") + ")", c("session_desktop_explain()")],
        ["On KDE: the KWin capture permission, with the code " + c("RX-KDE-001") + ", " + c("RX-KDE-002") + " or "
         + c("RX-KDE-003") + " and the remedy if it fails", c("kwin_check_permission()")],
        ["The clocks, the ghost-eviction threshold, the administrative session cap, the test tone when on", c("main.c")
         + ", " + c("wt_audio_test()")],
        ["The composition budget in force (" + c("budget") + ")", c("budget_startup_line()")],
        ["The video queue threshold, the frame-rhythm regulator, the dead-line values (" + c("wt") + ")",
         c("wt_clear_threshold()") + ", " + c("wt_adaptive_rate()") + ", " + c("wt_dead_line()")],
        ["The ban file and the number of addresses loaded", c("main.c")],
        ["The PAM helper, or the synchronous fallback", c("helper_turn_on()")],
        ["The child table switched on, or refused because the running binary was replaced (" + c("child") + ")",
         c("children_turn_on()")],
        ["What the parent passes to every child on its command line (" + c("child") + ")", c("children_phase9()")],
        ["The command socket, only if requested with the bench option " + c("--command-socket") + " (never in the packaged "
         "unit)", c("command_open()")],
        ["The PAM service file found, or " + c("⛔ the PAM service «remotix» DOES NOT EXIST"), c("look_pam_service()")],
        ["Certificates: generated or reused, fingerprints (" + c("cert") + ")", c("certificates_prepare()")],
        ["Desktops found alive from a previous server (reattach pending)", c("found_again_at_startup()")],
        [c("⭐ ready: https://<name>:<port>"), c("main.c")],
    ], "«TAB» — What the parent declares before serving") + \
    p("While running, the parent writes once a minute a cumulative line about the local-session guardian "
      "(" + c("guardian: calls=… worst_ms=… tenants=… loop_gaps=… worst_gap_ms=…") + ", period "
      + c("GUARDIAN_COUNT_MS") + " = 60,000 ms) instead of one line per two-second pass. At shutdown it sends the "
      "farewell " + c("RCP_SERVER_CLOSING") + " to every session and reports how many sessions did not finish "
      "within the wait (" + c("main.c") + ").")

# ── Environment variables ────────────────────────────────────────────────
S10 = p("REMOTIX reads almost nothing from the environment, on purpose. The complete list of names that start with "
        + c("REMOTIX_") + " in " + c("src/") + " and " + c("debian/") + ", leaving out the include guards of the "
        "headers (" + c("REMOTIX_*_H") + "), is in the table. Three are read with " + c("getenv()") + " by the "
        "product; two are service variables read by systemd; two are journal fields, not variables. Other occurrences "
        "of the prefix are not variables either: " + c("REMOTIX_BENCH") + " is a compile-time define (" + c("make BENCH=1")
        + "), " + c("REMOTIX_SPLIT") + " and " + c("REMOTIX_SGOMBRA_SOGLIA_MS") + " survive only in comments, and the "
        + c("REMOTIX_*") + " names in " + c("page.html") + " are JavaScript objects.",
        lead=True) + \
    table(["Name", "Effect", "Default", "File"], [
        [c("REMOTIX_PAM_LOG_TAG"), "Six lowercase hex digits: the tag that stands for a user name in the PAM check's "
         "own log line (" + c("user [a1b2c3]") + "). It is set by the PAM helper in the environment of the process that "
         "checks one login (" + c("setenv") + " from the request's tag) and <b>unset</b> when the request has none, so "
         "a value inherited from the server's environment is never used. A value that is not six hex digits is ignored "
         "and the line shows " + c("[??????]") + ".", "Unset; the helper sets it per login", c("helper.c")
         + " (sets), " + c("authentication.c") + " (reads, in " + c("name_for_log()") + ")"],
        [c("REMOTIX_VPP_PADDING"), "Value " + c("0") + " switches off the extra padding layers of the GPU "
         "RGB-to-NV12 conversion (the padding past the canvas is then left to the driver). Any other value or none: "
         "the layers are used, and are dropped by themselves for the encoder if the driver refuses them.",
         "Unset (layers used)", c("encoder.c") + " (in " + c("open_vpp()") + ")"],
        [c("REMOTIX_VULKAN_CONVERSION"), "Value " + c("copy") + " forces the copy route of the RGB-to-NV12 conversion "
         "even where the card can have the shader write the encoder input directly. For benches: it measures that "
         "route and exercises the branch other cards take.", "Unset (route read from the driver)", c("vulkanvideo.c")],
        [c("REMOTIX_PORT"), "Expanded by the unit into " + c("--port") + ".", c("7447"), c("debian/remotix.conf")
         + " (read by " + c("debian/remotix.service") + ")"],
        [c("REMOTIX_OPTIONS"), "Extra options appended to the server's command line, for example " + c("--name 192.168.1.10")
         + " for users who connect by address (the last " + c("--name") + " wins).", "Empty", c("debian/remotix.conf")
         + " (read by " + c("debian/remotix.service") + ")"],
        [c("REMOTIX_AREA") + ", " + c("REMOTIX_TENANT"), "Journal fields, not variables (" + rif("The systemd journal output") + ").",
         "—", c("log.c")],
    ], "«TAB» — Every REMOTIX_ name in the product") + \
    p("The administrator sets the two service variables in " + sysf("/etc/remotix/remotix.conf.d/*.conf") + ", which "
      "the unit reads after the defaults in " + sysf("/usr/share/remotix/remotix.conf") + " (" + c("EnvironmentFile")
      + " lines in " + c("debian/remotix.service") + "); a later file wins.") + \
    warn(c("REMOTIX_VPP_PADDING") + " and " + c("REMOTIX_VULKAN_CONVERSION") + " are read where the encoder opens. "
         "The encoder of a real session runs in the per-user child, whose environment " + c("become_and_exec()")
         + " builds from scratch (" + c("HOME") + ", " + c("USER") + ", " + c("LOGNAME") + ", " + c("PATH")
         + ", " + c("SHELL") + ", " + c("XDG_RUNTIME_DIR") + ", the bus address, and " + c("XDG_SESSION_ID") + " from PAM). "
         "Neither variable reaches a real session. They reach the startup probe (a fork of the parent) and the "
         "command " + c("remotix --encoding-test") + ", which is how the benches use them. "
         + c("rootside.c") + " (" + c("net_environment()") + ") does pass every " + c("REMOTIX_") + " variable of the root "
         "side to the network side, but the network side does not read any of them today.",
         "Which processes see these variables.") + \
    p("Other variables the code reads are the standard ones of the session it lives in: " + c("XDG_RUNTIME_DIR")
      + ", " + c("WAYLAND_DISPLAY") + ", " + c("DBUS_SESSION_BUS_ADDRESS") + ", " + c("XDG_STATE_HOME") + " (through "
      "GLib, for the session log), " + c("DCONF_PROFILE") + ", " + c("LANG") + ", " + c("PATH") + ", " + c("USER")
      + " and " + c("JOURNAL_STREAM") + " (" + c("log.c") + ", " + c("session.c") + ", " + c("kwin.c") + ", "
      + c("wlroots.c") + ", " + c("wlr_input.c") + ", " + c("child.c") + "). Variables used only by the test "
      "scripts are in " + rif("Testing") + ".")

# ── Diagnostic instruments ───────────────────────────────────────────────
S11 = p("Besides the log, the product carries a few instruments for diagnosis. None is on in the packaged service "
        "except " + c("--journal") + ": the unit's " + c("ExecStart") + " carries no bench option, and " + c("BENCH_ON")
        + " is 0 in " + c("rcp.c") + ".", lead=True) + \
    table(["Instrument", "What it answers", "How"], [
        [c("--verbose"), "What the transport, capture and encoder are doing frame by frame",
         "Add it through " + c("REMOTIX_OPTIONS") + ". It is passed to the root side, the PAM helper and every "
         "child. Detail lines never go to the journal."],
        [c("remotix --encoding-test"), "Can this card encode, by which route, with which codecs?",
         "Prints one JSON line: " + c('{"outcome":"hardware"|"none","encoder":…,"route":…,"node":…,"reason":…,"codec":…,'
         '"offered":…,"hevc":…,"h264":…,"hevc_route":…,"h264_route":…}') + " (" + c("child.c") + ")."],
        [c("--survey DIR"), "Is the picture the page paints the picture that was captured?", "Writes the captured frame "
         "and the encoded streams for pixel-comparison benches (bench option)."],
        [c("--command-socket PATH"), "Is the unblock socket alive?", "Answers " + c("PING") + " with " + c("PONG")
         + "; " + c("UNBLOCK <address>") + " removes a ban. Not in the packaged unit: see " + rif("Login and its defences") + "."],
        [c("GET /fingerprint"), "Which session certificate is in force?", "Served by " + c("page.c") + "."],
        ["The diagnostics mode of the page", "What the page itself knows: its counters, the chosen video route, the "
         "fallbacks it took", "See below."],
        ["Child command line", "With which settings was this child born?", sysf("/proc/<pid>/cmdline")
         + " of the child: the optional words " + c("--verbose") + " and " + c("--journal") + " are there."],
    ], "«TAB» — The instruments") + \
    h4("The diagnostics mode of the page") + \
    p("The page keeps a text log of its own decisions and counters in the element " + c("#logbook") + " (the function "
      + c("note()") + " in " + c("page.html") + " appends to it). Since 16 Aug 2026 it is <b>hidden by default</b>: the "
      "style rule " + c("body:not(.diagnostics) #logbook") + " hides it, and with it the small keyboard-shortcut button "
      "and its notice, which sat where users reach for the desktop's own controls. The text still accumulates in the "
      "DOM, so diagnostics do not depend on having been visible. It appears with " + c("?logbook") + " in the address, "
      "or from the browser console with " + c("REMOTIX.logbook(true)") + " (" + c("logbook_visible()") + "); "
      + c("REMOTIX.logbook(false)") + " hides it again. The same " + c("window.REMOTIX") + " object exposes "
      + c("viewer") + ", " + c("version") + " and the counters that the benches read; the comment in " + c("page.html")
      + " calls it an object to read, not a switch that changes the page's behaviour. The array " + c("SC_LOG")
      + " (at most " + c("SC_LOG_MAX") + " = 256 entries, exposed as " + c("REMOTIX.shortcuts.logbook") + ") keeps the notes of the "
      "keyboard-shortcut engine for the benches. The page's other query options "
      "(" + c("?video=…") + ", " + c("?canvas=…") + ", " + c("?draw=mse") + ", " + c("?layout=…") + ") are described in "
      + rif("The browser page") + ".") + \
    warn(c("?logbook") + " also arms a test-only hook: with it in the address, the fragment " + c("#video_fault=die|mute|blind")
         + " makes the video worker misbehave on purpose, to prove the fallback on a test machine. It is read only "
         "from the fragment (which never reaches the server) and only together with " + c("?logbook") + ", so a link "
         "without it cannot break anybody's video.", "A test hook behind the diagnostics switch.") + \
    h4("Reading a defect report") + \
    steps([
        "Read the startup declarations (" + rif("The startup declarations") + "): most «it does not work» cases are "
        "already named there: no codec offered, no PAM service file, the KWin permission missing.",
        "Filter by user (" + c("REMOTIX_TENANT") + " or the bracket) and by area; read " + c("budget") + " for refusals, "
        + c("rcp") + " for the handshake, " + c("session") + " and " + c("child") + " for the birth and the end of the desktop.",
        "For a refused login, tell " + c("PAM REFUSED") + " (a real no) from " + c("⛔ PAM COULD NOT JUDGE") + " (a missing "
        + sysf("/etc/pam.d/remotix") + " or a missing list file).",
        "For a desktop that is born and shows nothing, read the " + c("session") + " lines and the user's "
        + sysf("session.log") + ".",
        "Only then switch on " + c("--verbose") + ", for the shortest time that reproduces the defect.",
    ]) + \
    tip("a session that disappears leaves a line with the numbers it was closed on (the dead-line values, the clock that "
        "expired, the farewell code). A disappearance without such a line is a defect of REMOTIX by the project's own "
        "invariant I1.", "No silent exits.")

CHAPTER = ("Logging and diagnostics", [
    ("The log module", S1),
    ("Anatomy of a log line", S2),
    ("Log areas", S3),
    ("Whose line it is", S4),
    ("Where the log lines go", S5),
    ("The systemd journal output", S6),
    ("Journal priorities and the rule of the head mark", S6B),
    ("What never enters the log", S7),
    ("The startup declarations", S8),
    ("Environment variables read by the product", S10),
    ("Diagnostic instruments", S11),
])
